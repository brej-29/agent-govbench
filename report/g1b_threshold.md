# G1b threshold choice

G1b is Model Armor's prompt injection and jailbreak filter only. A template with the filter at LOW_AND_ABOVE reports a
confidence per text; a record is blocked at threshold T when its highest confidence is at least T. The rule was: pick
the threshold that maximizes block rate minus false positive rate, on train and validation records only, before
looking at test.

## Decision as made (2026-10-07, frozen; the 611 train and validation records that existed then)

| threshold | malicious records | block rate | benign records | false positive rate | difference |
|---|---|---|---|---|---|
| LOW | 175 | 54.9% | 426 | 48.6% | 6.3 |
| MEDIUM (chosen) | 175 | 42.9% | 426 | 29.8% | 13.1 |
| HIGH | 175 | 21.7% | 426 | 17.1% | 4.6 |

MEDIUM is also the threshold of G1's template, so G1b makes the same decisions as G1 on the test records.

## Post-hoc check on all final train and validation records (not used for any decision)

| threshold | malicious records | block rate | benign records | false positive rate |
|---|---|---|---|---|
| LOW | 867 | 55.4% | 2081 | 42.2% |
| MEDIUM | 867 | 38.6% | 2081 | 25.8% |
| HIGH | 867 | 24.0% | 2081 | 15.2% |

On the larger final set, LOW and MEDIUM are nearly tied (block rate minus false positive rate 13.2 and 12.8 points), and
every threshold blocks 15 to 42% of benign records. The choice of threshold does not change the conclusion: the
injection filter alone produces a high false positive rate in this setting.
