# Yellowstack: Your Real-Time Python Script Runner 🐍✨

![Yellowstack Logo](https://img.shields.io/badge/Yellowstack-Real--time%20Python%20Script%20Runner-yellow?style=flat&logo=python)

Welcome to **Yellowstack**, a powerful tool designed for automating Python script execution. This project focuses on real-time script running with scheduling, logging, and OpenAI-assisted debugging. Whether you are managing tasks in AWS, working with DevOps, or simply running Python scripts, Yellowstack can streamline your workflow.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Real-Time Execution**: Run your Python scripts in real-time, allowing for immediate feedback and results.
- **Scheduling**: Schedule scripts to run at specific times or intervals, ensuring tasks are completed without manual intervention.
- **Logging**: Keep track of script execution with detailed logs, making debugging easier.
- **OpenAI-Assisted Debugging**: Utilize OpenAI's capabilities to assist in debugging your scripts, improving your development process.
- **REST API**: Access Yellowstack's features programmatically through a REST API.
- **AWS Integration**: Seamlessly integrate with AWS services for cloud-based execution and management.

## Installation

To get started with Yellowstack, follow these steps:

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/shaymaaabdelrazik/yellowstack.git
   cd yellowstack
   ```

2. **Install Dependencies**:

   Use `pip` to install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Download and Execute the Latest Release**:

   You can download the latest release from the [Releases section](https://github.com/shaymaaabdelrazik/yellowstack/releases). Follow the instructions provided there to execute the script.

## Usage

### Running Scripts

To run a Python script, use the following command:

```bash
python yellowstack.py your_script.py
```

### Scheduling Scripts

You can schedule scripts using the built-in scheduler. For example, to run a script every hour:

```bash
python yellowstack.py schedule your_script.py --every hour
```

### Logging

Logs are stored in the `logs/` directory. You can view them to check the execution history of your scripts.

### OpenAI-Assisted Debugging

To use OpenAI for debugging, simply run:

```bash
python yellowstack.py debug your_script.py
```

This will provide suggestions and improvements for your script.

## API Reference

Yellowstack provides a REST API for programmatic access. Below are some of the key endpoints:

### GET /scripts

Retrieve a list of all scheduled scripts.

### POST /scripts

Schedule a new script. You need to provide the script name and schedule details in the request body.

### DELETE /scripts/{id}

Remove a scheduled script by its ID.

For detailed API documentation, refer to the `docs/api.md` file in the repository.

## Contributing

We welcome contributions to Yellowstack! If you would like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

Please ensure that your code adheres to our coding standards and includes tests where applicable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please reach out via GitHub or open an issue in the repository.

You can also visit the [Releases section](https://github.com/shaymaaabdelrazik/yellowstack/releases) for the latest updates and downloads.

Thank you for using Yellowstack! We hope it enhances your Python scripting experience.