# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 (2026-02-19)


### Features

* add Airline Agent Policy documentation ([8afaa85](https://github.com/codesque16/tau2/commit/8afaa852826e8ee8e91701a06604ec605a645e95))
* add auto-discovery for community-contributed experimental domains ([#160](https://github.com/codesque16/tau2/issues/160)) ([c2139e8](https://github.com/codesque16/tau2/commit/c2139e8840af55148e17e18b6938b3f6a0aaacc6))
* Add comprehensive changelog and automated release management system ([#58](https://github.com/codesque16/tau2/issues/58)) ([f8de30c](https://github.com/codesque16/tau2/commit/f8de30c298689cbe0117d76a378e7315a17e5bd8))
* enhance logging for tool execution and response handling ([0d58217](https://github.com/codesque16/tau2/commit/0d582170f9665341b4fc6a68198fbb04ab333cd9))
* enhance simulation metrics and cost tracking ([29df44b](https://github.com/codesque16/tau2/commit/29df44b8d74ed5bb5cb4cd3dee50cd89085f3849))
* **experiment:** Add hyperparam sweep experimental code ([#77](https://github.com/codesque16/tau2/issues/77)) ([558e6cd](https://github.com/codesque16/tau2/commit/558e6cd066d7bf05db587fa2dc1509765c7d03bc))
* **gym:** add Gymnasium-compatible interface for RL training ([0ed2fd8](https://github.com/codesque16/tau2/commit/0ed2fd8d830a20657d89ae9c2efcc94838aa7129))
* integrate Logfire observability and enhance database state logging ([44b9ebe](https://github.com/codesque16/tau2/commit/44b9ebe7d626d639f6270ce7c1256813e7f67117))
* update Airline Agent Policy and enhance cost tracking ([fe10472](https://github.com/codesque16/tau2/commit/fe10472c7a1eccc76e568e4e381e942e6211b3c8))


### Bug Fixes

* add missing gymnasium dependency ([#91](https://github.com/codesque16/tau2/issues/91)) ([a969a0c](https://github.com/codesque16/tau2/commit/a969a0c0a29bc47ba8580107932f5298ee636045))
* communicate_info fixed to nl_assertions in Mock domain tasks ([#66](https://github.com/codesque16/tau2/issues/66)) ([702ee77](https://github.com/codesque16/tau2/commit/702ee77e497d89e9d8942ab7206c1a465b12e503))
* Remove missing submissions from manifest and add images to public directory ([#55](https://github.com/codesque16/tau2/issues/55)) ([462578b](https://github.com/codesque16/tau2/commit/462578b06dcc143c6ad67f75ebe08662dcb98caf))
* update leaderboard submission validation and clarify submission types ([#155](https://github.com/codesque16/tau2/issues/155)) ([917227c](https://github.com/codesque16/tau2/commit/917227cedf029f1a659e339a860c738a530fd20e))

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.2.1] - 2025-11-07
### Added
- Gymnasium-compatible interface for RL training with `AgentGymEnv` and `UserGymEnv`
- Train/test task splits for all domains
- Interactive play mode (`tau2 play`) supporting both agent and user roles
- Possibility to strictly enforce communication protocol rules (e.g., no mixed messages with text and tool calls)

## [0.2.0] - 2025-10-06

### Added
- Web-based leaderboard system with interactive submission management
- GitHub Pages deployment for leaderboard with automated CI/CD
- Comprehensive submission validation and verification system
- Model comparison interface with performance metrics visualization
- Trajectory visualization in web interface
- Mobile-responsive leaderboard design
- Logo assets and branding for multiple LLM providers
- Live leaderboard deployment at tau-bench.com

### Changed
- Enhanced submission manifest structure
- Improved image handling and asset management
- Updated deployment workflow for better reliability

### Fixed
- Mobile view responsiveness issues
- Missing submissions from manifest
- Image path resolution for GitHub Pages deployment
- Base URL handling for subdirectory deployment

## [0.1.3] - 2025-08-26

### Fixed
- LLM arguments parsing and handling
- Removed default natural language assertion checks that were causing issues

## [0.1.2] - 2025-07-17

### Added
- `tau2 check-data` CLI command for verifying data directory setup
- Support for `TAU2_DATA_DIR` environment variable for non-editable installs
- Fallback to local source when data directory is not set
- `--num-tasks` CLI flag for limiting task count

### Changed
- Made `pip install -e .` the default installation method
- Improved task name display in CLI
- Enhanced data directory configuration flexibility

### Fixed
- Installation issues with data directory discovery
- Task filtering and display problems

## [0.1.1] - 2025-06-12

### Fixed
- Domain viewer CLI functionality
- `tau2 domain` command execution issues

## [0.1.0] - 2025-06-12

### Added
- Initial release of τ²-bench framework
- Support for multiple domains: mock, airline, retail, telecom
- Command-line interface with `tau2` command
- Agent evaluation system with LLM integration via LiteLLM
- User simulator for realistic conversation scenarios
- Environment system with domain-specific tools and policies
- Orchestration system for managing agent-user-environment interactions
- Comprehensive test suite
- Domain-specific documentation and API endpoints
- Experimental features: no-user mode, oracle-plan mode, workflow policies
- Support for ablation studies
- Interactive environment CLI for testing and debugging
- Caching system for LLM calls (Redis-based)
- Multi-trial evaluation with concurrent execution support

### Technical Details
- Python 3.10+ support
- FastAPI-based web services
- Pydantic data models
- Rich CLI with tabulated output
- Comprehensive logging with Loguru
- Performance metrics and visualization
- Configurable LLM backends
- Semantic versioning adoption

## Links
- [Repository](https://github.com/sierra-research/tau2-bench)
- [Leaderboard](https://tau-bench.com)
- [Paper](https://arxiv.org/abs/2506.07982)
- [Blog Post](https://sierra.ai/blog/benchmarking-agents-in-collaborative-real-world-scenarios)
