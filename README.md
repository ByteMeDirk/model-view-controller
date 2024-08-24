# Model View Controller (MVC) Database Schema Manager

This package provides a flexible and powerful tool for managing database schemas using a Model-View-Controller (MVC)
architecture. It allows you to define your database models using YAML configuration files and automatically build,
update, or drop database tables based on these configurations.

## Features

- **YAML-based Model Definition**: Define your database models using simple YAML configuration files.
- **Automatic Schema Management**: Create, update, or drop database tables based on your model definitions.
- **Schema Comparison**: Automatically detect and apply changes to existing tables.
- **Force Mode**: Option to force updates even when data loss might occur.
- **Flexible Column Types**: Support for a wide range of SQL column types.
- **Database Agnostic**: Works with any database supported by SQLAlchemy.
- **CLI Interface**: Easy-to-use command-line interface for managing your database schema.
- **Logging**: Detailed logging of all operations for easy troubleshooting.

## Installation

```bash
pip install model-view-controller
```

## Usage

### Directory Structure

Create a directory for your project with the following structure:

```
your_project/
├── config.yaml
├── model1.yaml
├── model2.yaml
└── ...
```

### Configuration

1. Create a `config.yaml` file in your project directory:

```yaml
database:
  connection: "postgresql://username:password@localhost:5432/dbname"
  schema: "public"
```

2. Define your models in separate YAML files:

```yaml
# users.yaml
columns:
  - name: id
    type: integer
    primary_key: true
    auto_increment: true
  - name: name
    type: string
    length: 100
  - name: email
    type: string
    length: 100
description: "Users table"
```

### CLI Commands

#### Build Schema

To build or update your database schema:

```bash
mvc build /path/to/your/project
```

Options:

- `--force`: Force column deletion even if it contains data
- `--drop-tables`: Drop tables that exist in the database but not in configs

#### Drop Schema

To drop all tables from the database schema:

```bash
mvc drop /path/to/your/project
```

Options:

- `--force`: Force drop without confirmation

## Advanced Features

### Column Type Mapping

The package supports a wide range of SQL column types, including:

- Integer types: `integer`, `bigint`, `smallint`
- String types: `string`, `text`
- Floating-point types: `float`, `real`, `double`, `decimal`, `numeric`
- Date and time types: `datetime`, `timestamp`, `time`, `date`
- Binary types: `binary`, `large_binary`
- Boolean type: `boolean`
- Unicode types: `unicode`, `unicode_text`

### Schema Comparison and Updates

When running the `build` command, the tool will:

1. Compare existing table schemas with the defined models
2. Add new columns as needed
3. Remove deleted columns (with confirmation or using `--force`)
4. Update column types if they have changed

### Logging

The package provides detailed logging of all operations, making it easy to track changes and troubleshoot issues.
