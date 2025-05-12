#!/usr/bin/env python3
import argparse
import sys
import time

def main():
    # Create command line argument parser
    parser = argparse.ArgumentParser(description='Test script for parameter functionality')

    # Add parameters, all with prefix --
    parser.add_argument('--name', type=str, help='Your name')
    parser.add_argument('--age', type=int, help='Your age')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--delay', type=int, default=0, help='Execution delay in seconds')

    # Parse command line arguments
    args = parser.parse_args()
    
    print("---------- SCRIPT PARAMETERS ----------")
    print(f"Received the following parameters:")

    if args.verbose:
        print(f"Verbose output mode enabled")
        print(f"All arguments: {sys.argv}")
    
    print(f"name: {args.name}")
    print(f"age: {args.age}")
    print(f"verbose: {args.verbose}")
    print(f"delay: {args.delay}")
    print("---------------------------------------")
    
    if args.delay and args.delay > 0:
        print(f"Waiting for {args.delay} seconds...")
        for i in range(args.delay):
            print(f"{args.delay - i} seconds remaining...")
            time.sleep(1)

    if args.name:
        greeting = f"Hello, {args.name}"
        if args.age:
            greeting += f", you are {args.age} years old!"
        else:
            greeting += "!"
        print(greeting)

    print("Script completed successfully!")

if __name__ == "__main__":
    main()