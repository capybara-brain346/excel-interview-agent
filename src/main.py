#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.ui.gradio_app import create_app


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("interview_app.log"),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Technical Interview System")
    parser.add_argument(
        "--mock", action="store_true", help="Use mock evaluator instead of LLM"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the Gradio app on (default: 7860)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the Gradio app on (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--share", action="store_true", help="Create a public link for the Gradio app"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    load_dotenv()

    try:
        app = create_app()

        print("""
🚀 Starting Technical Interview System
   Press Ctrl+C to stop the server
        """)

        app.launch(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            show_error=True,
            quiet=False,
        )

    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        print("\nInterview system stopped")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
