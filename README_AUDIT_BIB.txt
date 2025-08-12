Audit bibliographique – Kit d'application
Date: 2025-08-11T13:48:11

Contenu:
1) bibliography.cleaned.bib  — version nettoyée (dédoublonnée, clés conservées priorisant celles citées)
2) bibliography.cited.bib    — uniquement les références effectivement utilisées dans la biblio rendue
3) bibliography.extras.bib   — les entrées restantes (non citées)
4) citation_key_replacements.csv — mapping des clés à remplacer -> clé conservée
5) apply_bib_dedup.py        — script pour mettre à jour les clés dans vos fichiers .tex

Mode d'emploi (sans nous envoyer vos .tex) :
- Placez citation_key_replacements.csv et apply_bib_dedup.py à la racine de votre projet LaTeX.
- Exécutez :  python apply_bib_dedup.py . citation_key_replacements.csv
  (il parcourt récursivement tous les .tex et remplace les clés dans \cite, \parencite, \textcite, \autocite)
- Remplacez ensuite votre bibliographie par bibliography.cleaned.bib dans votre \addbibresource{...}.
- Recompilez : l’erreur de doublons disparaîtra et la biblio sera alignée.

Option : si vous voulez garder uniquement les références effectivement citées dans le manuscrit,
remplacez plutôt par bibliography.cited.bib (et archivez bibliography.extras.bib).

NB : si vous me fournissez le zip du projet LaTeX, je peux appliquer le patch directement et vous renvoyer un projet prêt à compiler.
