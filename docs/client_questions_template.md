# Client clarification email template

Use after the first validation pass. Only include questions that actually apply to the received file.

```text
Objet : Points à confirmer avant préparation du CSV WooCommerce

Bonjour,

J’ai contrôlé le fichier fournisseur. Avant de générer le fichier d’import, j’ai besoin de confirmer quelques points afin de ne rien inventer dans vos données :

1. [SKU / row] — [question]
2. [SKU / row] — [question]
3. [SKU / row] — [question]

Dès que j’ai ces confirmations, je finalise le CSV WooCommerce et le rapport de contrôle.

Aucun changement ne sera publié automatiquement dans la boutique.

Bien à vous,
Vladimir
```

Typical clarification topics:

- stock aliases (`RUPTURE`, `DISPO`, etc.);
- meaning of blank stock;
- ambiguous packaging;
- numeric Excel SKU / leading-zero confirmation;
- invalid or blank price;
- duplicate SKU;
- invalid/duplicate GTIN;
- missing variation attributes;
- rows without identifiers.
