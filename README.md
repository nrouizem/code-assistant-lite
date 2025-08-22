# Multi-Agent Code Assistant

**Current status**: This project is an early version of the [code assistant]([url](https://github.com/nrouizem/code-assistant)).

### Project Overview

This is a command-line code assistant that uses a team of AI agents to perform deep analysis of a software codebase. The objective is to leverage a multi-agent debate and critique process to produce insights that are offer greater depth than those of any single large language model.

This codebase will always be a code assistant; however, the long-term objective is to develop a "deep-think"-like ensemble of agents that is able to respond to prompts and inputs in any domain with insights that are hopefully superior to those of any single large language model. The code assistant is a first step in that direction; it will also be a tool to develop the general-purpose reasoning engine.

The code assistant is currently intentionally tailored to small (<5k LOC) codebases.

### Features

- **Multi-Agent Architecture**: Employs a team of specialized AI agents (Architects, a Devil's Advocate, a Synthesizer, etc.) that collaborate, debate, and critique each other's work to produce a robust final report. 

- **Dual Analysis Modes**:
    - **Audit Mode**: Performs a deep technical review to find bugs, security vulnerabilities, and implementation flaws. 
    - **Design Mode**: Brainstorms high-level, creative architectural directions and novel features for a project. 

- **Dynamic Specialist Selection**: Automatically analyzes the codebase to select the most relevant specialist agent (e.g., web_security_specialist, ai_systems_specialist) for the review team.
