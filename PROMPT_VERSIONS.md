# Prompt Versions Guide

## Overview

This system supports two versions of prompts for generating user stories:

- **v1 (Original)**: Basic prompts with standard output
- **v2 (Enhanced)**: Detailed, high-quality prompts with same structure as v1

**Both versions use the SAME JSON structure** - only the prompt instructions differ!

## Structure (Same for Both Versions)

```json
{
  "Epics": [
    {
      "User Story": "Detailed description of what the system must do...",
      "Deliverables": {
        "architecture_design": "Specific description...",
        "unit_tests": "Specific test description..."
      }
    }
  ]
}
```

## Version Comparison

| Aspect | v1 (Original) | v2 (Enhanced) |
|--------|---------------|---------------|
| **Structure** | User Story + Deliverables | User Story + Deliverables (SAME) |
| **User Story Length** | Variable, often short | 40-100 words (detailed) |
| **Deliverable Detail** | Basic descriptions | 20-50 words each (highly specific) |
| **Test Cases** | Basic format | IDs, detailed steps, specific expected results |
| **Definition of Done** | Simple strings | Arrays of 5-7 specific items (15-30 words each) |
| **Specificity** | Generic | References actual components, values, thresholds |

## v1 Example Output

```json
{
  "User Story": "The system must process data",
  "Deliverables": {
    "architecture_design": "Design of the processing module",
    "unit_tests": "Tests to ensure data processing works"
  }
}
```

**After refine_epics:**
```json
{
  "Deliverables": {
    "architecture_design": {
      "description": "Design of the processing module",
      "definition_of_done": "Design document completed and reviewed"
    }
  }
}
```

## v2 Example Output (Enhanced)

```json
{
  "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the electrical conductivity data provided by the sensor, so that insulin delivery can be precisely controlled.",
  "Deliverables": {
    "architecture_design": "Design of the continuous monitoring and data calculation modules within the insulin pump system, including sensor interface specifications and blood sugar calculation algorithms.",
    "database_schema_design": "Schema for storing and retrieving blood sugar data readings, calculation results, and historical trends to support real-time monitoring and analysis.",
    "unit_tests": "Tests to ensure the microsensor's data collection occurs continuously without interruption and blood sugar calculation accuracy is within required medical standards."
  }
}
```

**After refine_epics_v2:**
```json
{
  "Deliverables": {
    "architecture_design": {
      "description": "Design of the continuous monitoring and data calculation modules...",
      "definition_of_done": [
        "Complete system architecture diagram showing monitoring module, data calculation module, and sensor interface with all component interactions",
        "Detailed design document for blood sugar monitoring module including sensor data acquisition specifications and sampling frequency",
        "Detailed design document for blood sugar calculation module including algorithms for converting electrical conductivity to glucose levels",
        "Data flow diagrams showing how sensor readings move through the system to calculation output",
        "API specifications for all module interfaces including data formats and error codes",
        "Error handling and failover mechanisms documented for sensor disconnection scenarios",
        "Design reviewed and approved by technical lead and medical safety officer"
      ]
    }
  }
}
```

## Test Case Comparison

### v1 Test Cases
```json
{
  "test_cases": [
    {
      "requirement": "The system must monitor data",
      "test_case_1": {
        "description": "Test monitoring",
        "input": "Test data",
        "expected_output": "System monitors correctly"
      }
    }
  ]
}
```

### v2 Test Cases (Enhanced)
```json
{
  "test_cases": [
    {
      "requirement": "The insulin pump system must continuously monitor blood sugar levels",
      "test_cases": [
        {
          "id": "TC1",
          "description": "Verify that the microsensor continuously monitors blood sugar levels without interruption for 24 hours",
          "steps": [
            "Ensure the microsensor is properly implanted, calibrated, and connected to the monitoring system",
            "Start the monitoring process and record the start timestamp",
            "Monitor and log data output continuously for 24 hours without system intervention",
            "Review the complete data log for any gaps, missing readings, or interruptions"
          ],
          "expected_result": "Continuous data output captured every 5 minutes for full 24-hour period with zero gaps or missing data points"
        },
        {
          "id": "TC2",
          "description": "Check blood sugar reading accuracy against medical glucose meter",
          "steps": [
            "Collect simultaneous readings from microsensor and calibrated medical glucose meter",
            "Test at five different glucose levels: 70, 100, 150, 200, and 250 mg/dL",
            "Compare readings for each test point",
            "Calculate percentage difference"
          ],
          "expected_result": "Microsensor readings match glucose meter within ±5% margin across all tested concentrations"
        }
      ]
    }
  ]
}
```

## How to Switch Between Versions

Edit your `.env` file:

```bash
# Use enhanced v2 prompts (recommended for better quality)
USE_V2_PROMPTS=true

# Use original v1 prompts
USE_V2_PROMPTS=false
```

## When to Use Each Version

### Use v1 when:
- You need faster processing (simpler prompts = faster LLM responses)
- You have a very simple project with basic requirements
- You want to generate stories quickly and will manually refine them later

### Use v2 when:
- You want high-quality, production-ready user stories
- Your project has complex technical requirements
- You need detailed Definition of Done for each deliverable
- You want comprehensive test cases with specific steps
- You're working with medical, financial, or safety-critical systems

## Key v2 Enhancements

1. **Detailed User Stories**: 40-100 words with specific components, technologies, and benefits
2. **Specific Deliverables**: 20-50 words referencing actual system components
3. **Comprehensive DoD**: 5-7 actionable items per deliverable (15-30 words each)
4. **Structured Test Cases**: IDs, detailed steps (10-25 words), specific expected results (15-30 words)
5. **Quality Criteria**: Includes metrics, thresholds, accuracy standards
6. **Actionable**: Detailed enough for developers and QA to implement without clarification

## Recommendation

**Use v2 by default** (`USE_V2_PROMPTS=true`) for significantly better output quality with the same JSON structure!
