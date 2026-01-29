doc_text_raw = """
Insulin Pump
An insulin pump is a medical system that simulates the operation of the pancreas (an internal organ). The software controlling this system is an embedded system, which collects information from a sensor and controls a pump that delivers a controlled dose of insulin to a user.

People who suffer from diabetes use the system. Diabetes is a relatively common condition where the human pancreas is unable to produce sufficient quantities of a hormone called insulin. Insulin metabolizes glucose (sugar) in the blood. The conventional treatment of diabetes involves regular injections of genetically engineered insulin. Diabetics measure their blood sugar levels using an external meter and then calculate the dose of insulin that they should inject. The problem with this treatment is that the level of insulin required does not just depend on the blood glucose level but also on the time of the last insulin injection. This can lead to very low levels of blood glucose (if there is too much insulin) or very high levels of blood sugar (if there is too little insulin). Low blood glucose is, in the short term, a more serious condition as it can result in temporary brain malfunctioning and, ultimately, unconsciousness and death. In the long term, however, continual high levels of blood glucose can lead to eye damage, kidney damage, and heart problems.

Current advances in developing miniaturized sensors have meant that it is now possible to develop automated insulin delivery systems. These systems monitor blood sugar levels and deliver an appropriate dose of insulin when required. Insulin delivery systems like this already exist for the treatment of hospital patients. In the future, it may be possible for many diabetics to have such systems permanently attached to their bodies. 

A software-controlled insulin delivery system might work by using a microsensor embedded in the patient to measure some blood parameter that is proportional to the sugar level. This is then sent to the pump controller. This controller computes the sugar level and the amount of insulin that is needed. It then sends signals to a miniaturized pump to deliver the insulin via a permanently attached needle.

The blood sensor measures the electrical conductivity of the blood under different conditions and that these values can be related to the blood sugar level. The insulin pump delivers one unit of insulin in response to a single pulse from a controller. Therefore, to deliver 10 units of insulin, the controller sends 10 pulses to the pump.

Clearly, this is a safety-critical system. If the pump fails to operate or does not operate correctly, then the user’s health may be damaged or they may fall into a coma because their blood sugar levels are too high or too low. There are, therefore, two essential high-level requirements that this system must meet:
1. The system shall be available to deliver insulin when required.
2. The system shall perform reliably and deliver the correct amount of insulin to counteract the current level of blood sugar.

The system must therefore be designed and implemented to ensure that the system always meets these requirements. More detailed requirements and discussions of how to ensure that the system is safe are discussed in later chapters.

    """

expected_requirements = """
1. The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor.
2. The system must accurately calculate the blood sugar level from the data provided by the microsensor.
3. The system must determine the required dose of insulin based on the calculated blood sugar level and the timing of the last insulin injection.
4. The insulin pump must administer the correct amount of insulin as determined by the system's calculations.
5. The system must deliver insulin through a permanently attached needle, with one unit of insulin delivered per pulse from the controller.
6. The system must ensure that the insulin pump is always available to deliver insulin when required.
7. The system must perform reliably to prevent any harm to the user by avoiding over-delivery or under-delivery of insulin.
8. The system must ensure safety and prevent potential health risks such as coma by managing the user's blood sugar levels accurately.
9. The system must include integration testing to verify that all components work together as intended and meet the specified requirements.
"""

expected_epics = """"{
 "Epics": [
        {
            "User Story": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the data provided.",
            "Deliverables": {
                "architecture_design": "Design of the continuous monitoring and data calculation modules within the insulin pump system.",
                "database_schema_design": "Schema for storing and retrieving blood sugar data readings and calculation results.",
                "unit_tests": "Tests to ensure the microsensor's data collection and blood sugar calculation accuracy."
            }
        },
        {
            "User Story": "The system must determine the required dose of insulin based on the calculated blood sugar level and the timing of the last insulin injection, and administer the correct amount of insulin through a permanently attached needle, delivering one unit of insulin per pulse from the controller.",
            "Deliverables": {
                "architecture_design": "Design of the insulin dosage calculation and administration modules.",
                "database_schema_design": "Schema to log dosage calculations and insulin delivery records.",
                "unit_tests": "Tests to verify correct insulin dosage calculations and delivery mechanisms."
            }
        },
        {
            "User Story": "The system must ensure that the insulin pump is always available and performs reliably to deliver insulin when required, avoiding over-delivery or under-delivery to prevent any harm such as coma and manage the user's blood sugar levels safely.",
            "Deliverables": {
                "architecture_design": "Design of system reliability and safety features.",
                "production_support_plan": "Plan to ensure system uptime and reliability, including maintenance and emergency response strategies."
            }
        },
        {
            "User Story": "The system must include integration testing to verify that all components work together as intended and meet the specified requirements.",
            "Deliverables": {
                "user_training_documentation": "Documentation on how to conduct integration tests for system components.",
                "unit_tests": "Comprehensive tests to cover all system integration points."
            }
        }
    ]
}
"""

expected_tests = """
{
  "test_cases": [
    {
      "requirement": "The insulin pump system must continuously monitor the user's blood sugar levels using an implanted microsensor and accurately calculate the blood sugar level from the data provided.",
      "test_cases": [
        {
          "id": "TC1",
          "description": "Verify that the microsensor continuously monitors blood sugar levels without interruption.",
          "steps": ["Ensure the microsensor is properly implanted", "Monitor the output data continuously for 24 hours"],
          "expected_result": "Continuous data output without any gaps"
        },
        {
          "id": "TC2",
          "description": "Check the accuracy of the blood sugar level calculation against a known standard.",
          "steps": ["Collect data from the microsensor", "Compare the calculated blood sugar level with a medically approved glucose meter at various intervals"],
          "expected_result": "The blood sugar levels calculated by the system should match the readings from the glucose meter within an acceptable error margin"
        }
      ]
    },
    {
      "requirement": "The system must determine the required dose of insulin based on the calculated blood sugar level and the timing of the last insulin injection, and administer the correct amount through a permanently attached needle, with one unit of insulin delivered per pulse from the controller.",
      "test_cases": [
        {
          "id": "TC3",
          "description": "Verify that the system calculates the correct insulin dose based on current blood sugar level and the timing of the last dose.",
          "steps": ["Input various blood sugar levels and timings into the system", "Record the insulin dose calculated by the system"],
          "expected_result": "The calculated dose should match the expected dose as per medical guidelines"
        },
        {
          "id": "TC4",
          "description": "Confirm that the system administers the correct amount of insulin through the needle.",
          "steps": ["Trigger the insulin delivery mechanism", "Measure the amount of insulin delivered"],
          "expected_result": "The amount of insulin delivered should be exactly as calculated by the system"
        }
      ]
    },
    {
      "requirement": "The insulin pump must always be available and reliable to deliver insulin when required, ensuring it prevents any harm to the user by avoiding over-delivery or under-delivery of insulin.",
      "test_cases": [
        {
          "id": "TC5",
          "description": "Test the reliability and availability of the insulin pump under various conditions.",
          "steps": ["Simulate different operating conditions (e.g., low battery, high CPU usage)", "Attempt to deliver insulin"],
          "expected_result": "Insulin delivery should be successful and accurate under all tested conditions"
        }
      ]
    },
    {
      "requirement": "The system must ensure safety by accurately managing the user's blood sugar levels to prevent potential health risks such as coma.",
      "test_cases": [
        {
          "id": "TC6",
          "description": "Verify that the system maintains blood sugar levels within safe limits over an extended period.",
          "steps": ["Monitor and log blood sugar levels continuously for a week", "Check for any instances where levels go outside of safe boundaries"],
          "expected_result": "Blood sugar levels should remain within safe limits throughout the test period"
        }
      ]
    },
    {
      "requirement": "The system must include integration testing to verify that all components work together as intended and meet the specified requirements.",
      "test_cases": [
        {
          "id": "TC7",
          "description": "Perform integration testing of all system components.",
          "steps": ["Integrate all components", "Execute a series of operations involving all components", "Check for any failures or inconsistencies"],
          "expected_result": "All components should work together seamlessly without errors"
        }
      ]
    }
  ]
}
"""
