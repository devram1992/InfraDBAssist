# InfraDB Assist - CI/CD

## Overview

InfraDB Assist will use an automated CI/CD pipeline to build, test, scan, and deploy application changes.

## Pipeline

```text
Developer
   ↓
Git Repository
   ↓
CI Pipeline
   ├── Code Quality
   ├── Unit Tests
   ├── Security Scan
   └── Build Container Images
          ↓
      Image Registry
          ↓
   Deployment Pipeline
          ↓
      Kubernetes
          ↓
   Development / Test / Production
