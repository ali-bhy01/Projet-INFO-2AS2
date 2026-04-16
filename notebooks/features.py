"""
=============================================================
  ASRS — Advanced School Run Strategy  |  DAX 40 Futures
=============================================================

On travaille sur le backtest quantitatif d'une stratégie de
breakout intraday sur le DAX 40 (futures, résolution 5 min).

L'idée de base est simple : après les 4 premières bougies de
la session, le marché a donné une première indication de range.
On place un ordre d'achat au-dessus et un ordre de vente en
dessous. Le premier qui se déclenche, on le laisse courir
jusqu'à la fin de journée — sans target, juste un stop.

---------------------------------------------------------------
  RÈGLES FINALES (version optimisée — Sharpe 1.23)
---------------------------------------------------------------

  Signal bar  = 4ème bougie de 5min  →  ouvre à 09:15 CET
  Condition   = range de la bougie entre 10 et 55 pts

  Entrée long  = signal_high + 2   (buy-stop)
  Entrée short = signal_low  − 2   (sell-stop)
  → OCO : le premier déclenché annule l'autre

  Stop loss   = prix d'entrée opposé  (risque = range + 4 pts)
  Exit        = stop touché  OU  fin de journée à 17:30 CET
  Pas de profit target.

  Filtres actifs :
    F1 — on ne trade pas le vendredi
    F2 — on ne trade pas si range signal < 10 ou > 55 pts
    C4 — on ne trade pas en janvier, juillet, août

---------------------------------------------------------------
  RÉSULTATS DE RÉFÉRENCE  (2006–2026, dax-5m_bk.csv)
---------------------------------------------------------------

  Baseline (sans filtres)  →  Sharpe 0.40 | PF 1.08 | +6 029 pts | MaxDD −2 971
  + F1 + F2                →  Sharpe 0.83 | PF 1.17 | +8 051 pts | MaxDD −1 863
  + C4 (final)             →  Sharpe 1.23 | PF 1.27 | +9 278 pts | MaxDD −1 112

---------------------------------------------------------------
  FEATURES DISPONIBLES DANS dax-5m_bk.csv
---------------------------------------------------------------

  Le CSV ne contient pas de header. Format :
      DD/MM/YYYY ; HH:MM ; open ; high ; low ; close ; volume
  Timezone : CET (déjà en heure locale — 09:15 lisible directement)

  On peut construire les features suivantes à partir des données brutes :

  -- Signal bar (09:15 CET) --
  range_signal        = high - low                        # range de la bougie signal
  body_ratio          = |close - open| / range_signal     # proportion du corps
  close_position      = (close - low) / range_signal      # position du close dans le range (0=bas, 1=haut)
  direction_signal    = +1 si close > open, -1 sinon      # couleur de la bougie

  -- Contexte pré-session (bougies avant 09:15) --
  presession_move     = close_09h10 - close_08h00         # drift des 5 premières bougies
  presession_range    = max(high) - min(low) sur 08h00–09h10

  -- Gap d'ouverture --
  opening_gap         = open_09h00 - close_veille_17h30   # gap par rapport à la veille
  gap_direction       = signe du gap

  -- Volatilité historique --
  atr_20              = ATR moyen des 20 derniers jours
  range_vs_atr        = range_signal / atr_20              # range normalisé

  -- Calendrier --
  day_of_week         = 0 (lundi) à 4 (vendredi)
  month               = 1 à 12
  week_of_month       = 1 à 5

  -- Label (target à prédire) --
  pnl                 = points gagnés/perdus sur le trade du jour
  win                 = 1 si pnl > 0, 0 sinon
  exit_reason         = "stop" ou "eod"

---------------------------------------------------------------
  PISTES D'AMÉLIORATION À EXPLORER
---------------------------------------------------------------

  On peut essayer de prédire, avant d'entrer en trade :
    → Est-ce que ce jour va être profitable ?  (classification)
    → Quel PnL espéré ?                        (régression)

  Modèles à tester : logistic regression, random forest, XGBoost
  Attention au data leakage : toutes les features doivent être
  calculées AVANT 09:15, jamais avec des données post-signal.

  Variable cible conseillée pour commencer : win (0/1)
  Metric principale : Sharpe sur l'equity curve filtrée

"""
