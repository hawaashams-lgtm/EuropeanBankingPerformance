# Tableau Calculated Fields

The calculations below support the profitability, asset-growth and benchmark views. The final section records the checks used in the private development workbook.

## Profitability measures

### Net Interest Margin

```tableau
IF [Indicator] = "Net interest margin" THEN [Values] END
```

### Return on Equity

```tableau
IF [Indicator] = "Return on equity (RoE)" THEN [Values] END
```

These fields place two indicators from the long source table on separate scatter-plot axes. Each mark represents one geography-quarter observation.

## Total-asset growth

### Start Assets

```tableau
{ FIXED [Geography] :
    MAX(
        IF [Indicator] = "Total assets"
        AND [Time Period] = "2020Q2"
        THEN [Values]
        END
    )
}
```

### Latest Assets

```tableau
{ FIXED [Geography] :
    MAX(
        IF [Indicator] = "Total assets"
        AND [Time Period] = "2026Q1"
        THEN [Values]
        END
    )
}
```

### Baseline Asset Index

```tableau
100
```

### Latest Asset Index

```tableau
([Latest Assets] / [Start Assets]) * 100
```

### Asset Growth

```tableau
([Latest Assets] - [Start Assets]) / [Start Assets]
```

The FIXED expressions return one starting and one latest asset value for each geography. Rebased indices make proportional growth comparable even though the original asset totals differ greatly in size.

## SSM benchmark comparison

### SSM Benchmark 2026 Q1

```tableau
{ FIXED [Indicator] :
    MAX(
        IF [Geography] = "SSM"
        AND [Time Period] = "2026Q1"
        THEN [Values]
        END
    )
}
```

### Index vs SSM

```tableau
IF [Time Period] = "2026Q1" THEN
    ([Values] / [SSM Benchmark 2026 Q1]) * 100
END
```

### Deviation from SSM

```tableau
([Values] / [SSM Benchmark 2026 Q1]) - 1
```

`Deviation from SSM` is a relative difference. For example, `0.06` means the geography is 6% above the SSM value; it does not mean six percentage points above it.

## Stage 2 selected periods

```tableau
IF [Time Period] = "2020Q2"
OR RIGHT([Time Period], 2) = "Q4"
OR [Time Period] = "2026Q1"
THEN [Time Period]
END
```

This preserves the baseline, annual checkpoints, and latest observation without presenting all 24 quarters in the highlight table.

## Development data-audit logic

### Check for missing data

```tableau
IF ISNULL([Date])
OR ISNULL([Time Period])
OR ISNULL([Geography])
OR ISNULL([Indicator])
OR ISNULL([Values])
THEN 1
ELSE 0
END
```

### Duplicates

```tableau
{ FIXED [Time Period], [Geography], [Indicator] : COUNT([Series]) }
```

The expected value is `1`. Values above `1` would indicate duplicated analytical keys.

### Quarterly Coverage

```tableau
{ FIXED [Geography], [Indicator] : COUNTD([Time Period]) }
```

The expected result is `24` for every geography-indicator series.

## Formatting rule

Ratio values are already expressed in percentage units in the ECB file. They use a custom `%` suffix in Tableau. Tableau's standard Percentage format must not be used because it would multiply values such as `16.95` by 100.
