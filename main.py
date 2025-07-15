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

from src.utils.config_manager import ConfigManager
from src.utils.logger_setup import setup_logging
from src.processors.content_processor import ContentProcessor


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
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger('accessibility_assistant')
    
    try:
        # Load configuration
        config = ConfigManager()
        
        # Initialize processor
        processor = ContentProcessor(config)
        
        # Process file
        logger.info(f"Processing file: {args.file_path}")
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
                logger.info(f"Summary saved to: {args.output}")
            else:
                print("\n" + "="*60)
                print("ACCESSIBILITY SUMMARY")
                print("="*60)
                print(result['summary'])
                print("="*60)
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
