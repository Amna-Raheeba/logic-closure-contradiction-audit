Logic Closure Contradiction Audit -- report
===========================================
Log: standard-chain_breaker-3 (88 items, 126 declared relations, 322 logically linked pairs)

Closure violations: 13 (3 direct, 10 transitive)
Directly broken declared relations: 3
Violation rate over linked pairs: 0.040
Confidence-weighted violation rate: 0.043

Violations (pair, witness path):
  i027 x i032 [transitive, 2 edges] (conf 0.93 / 0.83)
    i027=yes -[subset]-> i028=yes -[exclusion]-> i032=no
  i028 x i032 [direct] (conf 0.88 / 0.83)
    i028=yes -[exclusion]-> i032=no
  i032 x i033 [transitive, 3 edges] (conf 0.83 / 0.79)
    i032=yes -[exclusion]-> i028=no -[subset]-> i027=no -[negation]-> i033=yes
  i032 x i035 [transitive, 2 edges] (conf 0.83 / 0.84)
    i032=yes -[exclusion]-> i028=no -[subset]-> i035=no
  i054 x i056 [transitive, 2 edges] (conf 0.81 / 0.95)
    i054=yes -[subset]-> i055=yes -[subset]-> i056=yes
  i055 x i056 [direct] (conf 0.81 / 0.95)
    i055=yes -[subset]-> i056=yes
  i056 x i059 [transitive, 3 edges] (conf 0.95 / 0.88)
    i056=no -[subset]-> i055=no -[subset]-> i054=no -[negation]-> i059=yes
  i056 x i061 [transitive, 2 edges] (conf 0.95 / 0.78)
    i056=no -[subset]-> i055=no -[subset]-> i061=no
  i070 x i073 [transitive, 3 edges] (conf 0.84 / 0.95)
    i070=yes -[subset]-> i071=yes -[subset]-> i072=yes -[subset]-> i073=yes
  i071 x i073 [transitive, 2 edges] (conf 0.84 / 0.95)
    i071=yes -[subset]-> i072=yes -[subset]-> i073=yes
  i072 x i073 [direct] (conf 0.91 / 0.95)
    i072=yes -[subset]-> i073=yes
  i073 x i076 [transitive, 4 edges] (conf 0.95 / 0.84)
    i073=no -[subset]-> i072=no -[subset]-> i071=no -[subset]-> i070=no -[negation]-> i076=yes
  i073 x i078 [transitive, 3 edges] (conf 0.95 / 0.79)
    i073=no -[subset]-> i072=no -[subset]-> i071=no -[subset]-> i078=no

Minimal correction set: 3 item(s) (exact)
  flip i032: entity e3 is in category C8 (recorded yes, conf 0.83)
  flip i056: entity e6 is in category C0 (recorded no, conf 0.95)
  flip i073: entity e8 is in category C0 (recorded no, conf 0.95)
Greedy correction set size: 3
