# Controller Agent POC Benchmark

## Overview

This benchmark validates the Controller Agent POC by comparing LLM analysis against manually-created gold standards.

## Test Fixtures

Located in `tests/fixtures/controllers/`:
- 12 Java Controller files covering various Spring MVC patterns
- Progressive complexity from simple to edge cases
- All major annotations covered (@Controller, @RestController, @GetMapping, etc.)

## Gold Standards

Located in `tests/fixtures/gold_standard/`:
- 12 manually-analyzed JSON files
- Follow exact schema from prompt template
- Include confidence scores and detailed notes

## Running the Benchmark

### Prerequisites

1. **Python 3.10+** with required packages:
   ```bash
   pip install anthropic pyyaml
   ```

2. **Anthropic API Key**:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

   Or create a `.env` file in project root:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Configuration**: Ensure `config/config.yaml` is properly configured with:
   - LLM model settings
   - Cost thresholds
   - Cache settings

### Execute Benchmark

```bash
cd tests
python benchmark_controller.py
```

## Success Criteria

The POC is considered successful if:

✅ **Accuracy >= 90%**: Mapping F1 score should be 90% or higher
✅ **Cost <= $1**: Total cost for ~12-20 files should be under $1
✅ **Cache Hit Rate**: Expected 60-80% on subsequent runs

## Output

### Console Report

A formatted report showing:
- Overall accuracy metrics (precision, recall, F1)
- Cost breakdown (total, per-file average)
- Model distribution (Haiku/Sonnet/Opus usage %)
- POC success criteria results
- Per-file detailed results

Example:
```
╔══════════════════════════════════════════════════════════════╗
║         Controller Agent POC Benchmark Report               ║
╚══════════════════════════════════════════════════════════════╝

📊 OVERALL METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Files Analyzed:  12
  Total Cost:            $0.45
  Average Cost/File:     $0.0375

🎯 ACCURACY METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Mapping F1 Score:      94.5%
  Dependency F1 Score:   96.2%

✅ POC SUCCESS CRITERIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Accuracy >= 90%:     ✅ PASS (94.5%)
  ✓ Cost <= $1 for 20:   ✅ PASS ($0.45)
```

### Saved Files

1. **Report**: `output/benchmark_report_TIMESTAMP.txt`
   - Human-readable benchmark report

2. **Results**: `output/benchmark_results_TIMESTAMP.json`
   - Machine-readable detailed results
   - Per-file metrics and comparisons

3. **Costs**: `output/benchmark_cost_tracker.jsonl`
   - JSONL log of all API calls and costs

4. **Cache**: `.cache/`
   - Cached LLM responses (speeds up re-runs)

## Interpreting Results

### Precision vs Recall

- **Precision**: Of all mappings the LLM found, how many were correct?
- **Recall**: Of all actual mappings, how many did the LLM find?
- **F1 Score**: Harmonic mean of precision and recall

### Model Distribution

- **70%+ Haiku**: Good - most queries handled by cheapest model
- **20-30% Sonnet**: Normal - some escalation for complex cases
- **<5% Opus**: Ideal - minimal use of most expensive model

If Opus usage is high (>10%), consider:
- Adjusting confidence thresholds
- Improving prompt templates
- Adding more few-shot examples

### Cost Analysis

Expected costs (approximate):
- **Haiku**: ~$0.02 per file
- **Sonnet**: ~$0.08 per file
- **Opus**: ~$0.30 per file

Total expected: **$0.30 - $0.60** for 12 files

If costs are higher:
- Check token usage (input + output)
- Verify prompt isn't excessively long
- Review if escalations are necessary

## Troubleshooting

### "No gold standard for X"
- Ensure gold standard JSON files match fixture filenames
- Check `tests/fixtures/gold_standard/` directory

### "ANTHROPIC_API_KEY not set"
- Export environment variable or create `.env` file
- Verify key is valid

### "Config file not found"
- Ensure `config/config.yaml` exists
- Check working directory is project root

### Low Accuracy (<90%)
- Review failed cases in detailed results JSON
- Check if prompt template needs improvement
- Verify few-shot examples are representative
- Consider adding more domain-specific examples

### High Costs (>$1)
- Review model distribution - too much Opus usage?
- Check confidence thresholds in config
- Verify cache is working (re-run should be cheaper)

## Next Steps After Benchmark

### If POC PASSES (≥90% accuracy, ≤$1 cost):
1. Proceed to **Phase 3**: Implement remaining agents (JSP, Service, Mapper, Procedure)
2. Maintain same quality standards
3. Build knowledge graph integration

### If POC FAILS:
1. Analyze failure patterns in results JSON
2. Refine prompt templates based on errors
3. Add targeted few-shot examples
4. Adjust confidence thresholds if needed
5. Re-run benchmark until criteria met

## Test Coverage

Current test fixtures cover:

✅ Simple @Controller with @Autowired
✅ @RestController with @RequestBody
✅ Multiple @RequestParam with defaults
✅ Constructor injection
✅ Multiple path variables
✅ No package statement (edge case)
✅ Mixed dependency injection types
✅ Complex nested generics
✅ @PatchMapping
✅ No class-level mapping
✅ Full CRUD resource controller
✅ Edge cases (@RequestHeader, @MatrixVariable, wildcards)

Missing coverage (consider adding):
- Session/Model attributes
- Exception handlers (@ExceptionHandler)
- Cross-origin (@CrossOrigin)
- Request/Response headers customization
- File upload (@MultipartFile)
