#!/usr/bin/env python3
"""
Standalone PDF to Markdown Converter using pymupdf4llm

This script converts PDF files to markdown format without using AI tokens.
The conversion is done entirely through pymupdf4llm library calls.

Usage:
    python pdf_to_markdown_converter.py input.pdf [options]

Options:
    --output OUTPUT     Output markdown file path (default: input_file.md)
    --no-convert        Skip conversion, just download/copy PDF
    --page-chunks       Split output by pages (creates multiple files)
    --write-images      Extract and save images from PDF
    --batch DIRECTORY   Convert all PDFs in directory

Returns:
    JSON output with conversion results for programmatic use
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    import pymupdf4llm
except ImportError:
    print("Error: pymupdf4llm not installed. Install with: pip install pymupdf4llm", file=sys.stderr)
    sys.exit(1)


def convert_pdf_to_markdown(
    pdf_path: str,
    output_path: Optional[str] = None,
    page_chunks: bool = False,
    write_images: bool = False
) -> Dict[str, Union[str, int, float, bool]]:
    """
    Convert a PDF file to markdown format.

    Args:
        pdf_path: Path to the PDF file
        output_path: Optional output path for markdown file
        page_chunks: If True, split output by pages
        write_images: If True, extract and save images

    Returns:
        Dictionary with conversion results
    """
    start_time = time.time()

    # Verify input file exists
    if not os.path.exists(pdf_path):
        return {
            "success": False,
            "error": f"File not found: {pdf_path}"
        }

    # Determine output path
    if output_path is None:
        output_path = str(Path(pdf_path).with_suffix('.md'))

    try:
        # Convert PDF to markdown using pymupdf4llm
        if page_chunks:
            # Convert with page chunks - returns list of dicts
            markdown_data = pymupdf4llm.to_markdown(
                pdf_path,
                page_chunks=True,
                write_images=write_images
            )

            # Save each page as separate file
            base_output = Path(output_path).stem
            output_dir = Path(output_path).parent

            for i, page_data in enumerate(markdown_data):
                page_file = output_dir / f"{base_output}_page_{i+1}.md"
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(page_data['text'])

            # Also save combined version
            combined_text = '\n\n'.join([p['text'] for p in markdown_data])
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(combined_text)

            conversion_time = time.time() - start_time

            return {
                "success": True,
                "input_file": pdf_path,
                "output_file": output_path,
                "page_files": [str(output_dir / f"{base_output}_page_{i+1}.md")
                              for i in range(len(markdown_data))],
                "num_pages": len(markdown_data),
                "total_characters": len(combined_text),
                "conversion_time": round(conversion_time, 2),
                "method": "pymupdf4llm_page_chunks"
            }
        else:
            # Simple conversion - returns string
            markdown_text = pymupdf4llm.to_markdown(
                pdf_path,
                write_images=write_images
            )

            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)

            conversion_time = time.time() - start_time

            return {
                "success": True,
                "input_file": pdf_path,
                "output_file": output_path,
                "total_characters": len(markdown_text),
                "conversion_time": round(conversion_time, 2),
                "method": "pymupdf4llm"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "input_file": pdf_path
        }


def batch_convert_directory(
    directory: str,
    output_dir: Optional[str] = None,
    page_chunks: bool = False,
    write_images: bool = False
) -> Dict[str, Union[List, int, float]]:
    """
    Convert all PDF files in a directory to markdown.

    Args:
        directory: Directory containing PDF files
        output_dir: Optional output directory for markdown files
        page_chunks: If True, split output by pages
        write_images: If True, extract and save images

    Returns:
        Dictionary with batch conversion results
    """
    start_time = time.time()

    # Verify directory exists
    if not os.path.isdir(directory):
        return {
            "success": False,
            "error": f"Directory not found: {directory}"
        }

    # Set output directory
    if output_dir is None:
        output_dir = os.path.join(directory, 'markdown')

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Find all PDF files
    pdf_files = list(Path(directory).glob('*.pdf'))

    if not pdf_files:
        return {
            "success": False,
            "error": f"No PDF files found in directory: {directory}"
        }

    results = []
    successful = 0
    failed = 0

    for pdf_file in pdf_files:
        output_file = os.path.join(output_dir, f"{pdf_file.stem}.md")
        result = convert_pdf_to_markdown(
            str(pdf_file),
            output_file,
            page_chunks=page_chunks,
            write_images=write_images
        )
        results.append(result)

        if result["success"]:
            successful += 1
        else:
            failed += 1

    total_time = time.time() - start_time

    return {
        "success": True,
        "directory": directory,
        "output_directory": output_dir,
        "total_files": len(pdf_files),
        "successful_conversions": successful,
        "failed_conversions": failed,
        "total_time": round(total_time, 2),
        "files": results
    }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Convert PDF files to Markdown format using pymupdf4llm'
    )
    parser.add_argument(
        'input',
        help='Input PDF file or directory (with --batch)'
    )
    parser.add_argument(
        '--output',
        help='Output markdown file path (default: input_file.md)'
    )
    parser.add_argument(
        '--no-convert',
        action='store_true',
        help='Skip conversion, just copy PDF'
    )
    parser.add_argument(
        '--page-chunks',
        action='store_true',
        help='Split output by pages (creates multiple files)'
    )
    parser.add_argument(
        '--write-images',
        action='store_true',
        help='Extract and save images from PDF'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Convert all PDFs in the specified directory'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for batch conversion'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Handle no-convert option
    if args.no_convert:
        result = {
            "success": True,
            "message": "Conversion skipped as requested",
            "input_file": args.input
        }
    elif args.batch:
        # Batch conversion mode
        result = batch_convert_directory(
            args.input,
            args.output_dir,
            args.page_chunks,
            args.write_images
        )
    else:
        # Single file conversion
        result = convert_pdf_to_markdown(
            args.input,
            args.output,
            args.page_chunks,
            args.write_images
        )

    # Output results
    if args.json or not sys.stdout.isatty():
        # Output as JSON for programmatic use
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if result["success"]:
            if args.no_convert:
                print(f"✓ Conversion skipped for: {args.input}")
            elif args.batch:
                print(f"✓ Batch conversion completed:")
                print(f"  Directory: {result['directory']}")
                print(f"  Files processed: {result['total_files']}")
                print(f"  Successful: {result['successful_conversions']}")
                print(f"  Failed: {result['failed_conversions']}")
                print(f"  Time: {result['total_time']}s")
                print(f"  Output: {result['output_directory']}")
            else:
                print(f"✓ Successfully converted: {result['input_file']}")
                print(f"  Output: {result['output_file']}")
                print(f"  Characters: {result['total_characters']:,}")
                print(f"  Time: {result['conversion_time']}s")
                if 'num_pages' in result:
                    print(f"  Pages: {result['num_pages']}")
        else:
            print(f"✗ Conversion failed: {result['error']}", file=sys.stderr)
            sys.exit(1)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())