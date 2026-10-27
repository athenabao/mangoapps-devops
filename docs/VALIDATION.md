# Starter validation

Prepared October 26, 2026, Pacific time.

| Check performed locally | Result |
| --- | --- |
| Automated application tests | 8 passed |
| Add, read, complete and delete tasks | Passed |
| Persistence across application recreation | Passed |
| Database table missing / database file missing during runtime | Health returns HTTP 503 |
| Input escaping, SQL parameters, form-token handling and task limit | Passed |
| Missing production secret | Startup rejected as expected |
| Gunicorn in production mode, serving HTTP app and /health | Passed |
| CloudFormation validation with cfn-lint 1.58.0 for us-west-2 | Passed |
| Provisioning script and embedded user-data shell syntax | Passed |
| Relative documentation links | Passed |
| Architecture SVG render and visual inspection | Passed |

Local app execution used Python 3.12. The target host installs Python 3.11;
the pinned packages' Python requirements support that version.

## Still required in your accounts

- Create the GitHub repository and deploy the CloudFormation stack.
- Verify package installation, resource signaling and Session Manager on the actual AMI.
- Test public reachability, CRUD, health and persistence on EC2.
- Confirm the account's credits, regional prices, budget and ongoing cost coverage.
- Verify the UI in your browser. Automated browser testing was unavailable because
  the validation environment could not download its browser executable.
- Record the demo and complete the README deployment table.

Template validation and local tests do not prove that an AWS deployment works.
Use the live acceptance checklist before submitting the project.
