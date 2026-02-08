# Program Landscape Report

An interactive Quarto-based analysis of the CaRMS program landscape, demonstrating data exploration and visualization skills.

## Sections

1. **Setup** — Connect to PostgreSQL and load program data with pandas
2. **Discipline Distribution** — Bar chart of programs per discipline, CMG/IMG grouped breakdown
3. **Geographic Accessibility** — Treemap of training sites, school × discipline heatmap
4. **Stream Availability** — CMG vs IMG crosstab, identifies disciplines without IMG streams
5. **Description Text Analysis** — Section fill rates, markdown length distribution
6. **Summary Findings** — Key statistics and coverage metrics

## Rendering

To generate the HTML report:

```bash
make report
```

Or manually:

```bash
quarto render reports/program_landscape.qmd --to html
```

The rendered HTML will be created at `reports/program_landscape.html`.

## Requirements

- [Quarto CLI](https://quarto.org/docs/get-started/) installed
- Python environment with pandas, plotly, and sqlalchemy
- CaRMS database running with ETL data loaded
