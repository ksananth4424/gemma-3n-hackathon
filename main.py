"""
Windows Accessibility Assistant - Main Entry Point
Provides AI-powered content summarization for neurodivergent users
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bootstrap import get_bootstrap, setup_ollama_models


def main():
    """Main entry point for command-line processing"""
    parser = argparse.ArgumentParser(
        description='Windows Accessibility Assistant - Content Processor'
    )
    parser.add_argument('file_path', help='Path to file to process')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--format', '-f', choices=['text', 'html', 'json'], 
                       default='text', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--setup-models', action='store_true',
                       help='Setup Ollama models and exit')
    
    args = parser.parse_args()
    
    try:
        # Initialize application
        bootstrap = get_bootstrap()
        
        # Setup models if requested
        if args.setup_models:
            print("Setting up Ollama models...")
            setup_ollama_models()
            print("Model setup completed!")
            return
        
        # Perform health check
        if not bootstrap.health_check():
            print("ERROR: Application health check failed!")
            print("Please ensure Ollama is running and models are available.")
            print("Try running: python main.py --setup-models")
            sys.exit(1)
        
        # Get content processor
        processor = bootstrap.get_content_processor()
        
        # Process file
        print(f"Processing file: {args.file_path}")
        result = processor.process_file(args.file_path)
        
        if result['success']:
            # Output result
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    if args.format == 'json':
                        import json
                        json.dump(result, f, indent=2)
                    else:
                        f.write(result['summary'])
                print(f"Summary saved to: {args.output}")
            else:
                print("\n" + "="*60)
                print("ACCESSIBILITY SUMMARY")
                print("="*60)
                print(result['summary'])
                print("="*60)
                print(f"\nProcessing time: {result['metadata']['processing_time']:.2f}s")
                print(f"Content type: {result['content_type']}")
        else:
            print(f"ERROR: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean shutdown
        try:
            bootstrap = get_bootstrap()
            bootstrap.shutdown()
        except:
            pass


if __name__ == "__main__":
    main()
