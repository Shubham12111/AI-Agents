#!/usr/bin/env python3
"""
Main runner script for the analysis workflow
"""
from services.agent_service.run_analysis import run_analysis_workflow

if __name__ == "__main__":
    try:
        collection_id = run_analysis_workflow()
        print(
            f"\nAll results have been saved to MongoDB with collection ID: {collection_id}"
        )
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
