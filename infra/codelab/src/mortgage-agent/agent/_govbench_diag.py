"""GOVBENCH diagnostic: log TLS trust settings and the certificate the egress gateway presents. Logs only."""
import logging
import os
import socket
import ssl

log = logging.getLogger("govbench.diag")


HOSTS = ["telemetry.mtls.googleapis.com", "telemetry.googleapis.com", "aiplatform.googleapis.com",
         "aiplatform.mtls.googleapis.com", "agentregistry.googleapis.com", "agentregistry.mtls.googleapis.com",
         "oauth2.googleapis.com", "legacy-dms-HASH-uc.a.run.app", "www.example.com"]


def run() -> None:
    log.warning("GOVBENCH_DIAG mtls env: %s", {k: v for k, v in os.environ.items() if "MTLS" in k or "CLIENT_CERT" in k or "PROXY" in k.upper()})
    for h in HOSTS:
        _probe(h)


def _probe(host: str) -> None:
    try:
        b = os.environ.get("REQUESTS_CA_BUNDLE", "")
        log.warning("GOVBENCH_DIAG env REQUESTS_CA_BUNDLE=%s SSL_CERT_FILE=%s exists=%s cwd=%s ls=%s",
                    b, os.environ.get("SSL_CERT_FILE"), os.path.exists(b) if b else None, os.getcwd(),
                    sorted(os.listdir("/code"))[:30] if os.path.isdir("/code") else None)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, 443), timeout=10) as s, ctx.wrap_socket(s, server_hostname=host) as t:
            der = t.getpeercert(binary_form=True)
        import tempfile, subprocess
        with tempfile.NamedTemporaryFile("wb", suffix=".der", delete=False) as f:
            f.write(der)
        try:
            from cryptography import x509
            c = x509.load_der_x509_certificate(der)
            try:
                san = c.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)[:5]
            except Exception:  # noqa: BLE001
                san = None
            log.warning("GOVBENCH_DIAG %s peer subject=%s issuer=%s san=%s", host, c.subject.rfc4514_string(), c.issuer.rfc4514_string(), san)
        except Exception as e:  # noqa: BLE001
            log.warning("GOVBENCH_DIAG peer cert parse failed: %s (len=%d)", e, len(der))
        for name, path in (("bundle", b), ("system", "/etc/ssl/certs/ca-certificates.crt")):
            if path and os.path.exists(path):
                v = ssl.create_default_context(cafile=path)
                try:
                    with socket.create_connection((host, 443), timeout=10) as s, v.wrap_socket(s, server_hostname=host):
                        log.warning("GOVBENCH_DIAG %s verify with %s OK", host, name)
                except Exception as e:  # noqa: BLE001
                    log.warning("GOVBENCH_DIAG %s verify with %s FAILED: %s", host, name, e)
    except Exception as e:  # noqa: BLE001
        log.warning("GOVBENCH_DIAG %s failed: %s", host, e)
