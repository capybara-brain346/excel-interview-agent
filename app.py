#!/usr/bin/env python3

import sys
import argparse
from src.app import launch_app


def main():
    parser = argparse.ArgumentParser(
        description="Launch Excel Interview Agent Gradio App"
    )
    parser.add_argument(
        "--share", action="store_true", help="Create a public shareable link"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=7860, help="Port to bind to (default: 7860)"
    )

    args = parser.parse_args()

    print("🚀 Launching Excel Interview Agent...")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")

    if args.share:
        print("🌐 Creating public shareable link...")

    try:
        launch_app(share=args.share, server_name=args.host, server_port=args.port)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
