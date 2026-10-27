# Demo guide - aim for 3 to 4 minutes

These are prompts, not claims that your deployment has already succeeded.
Use your actual URLs, deployed values, checks and cost information.
Read the code and explain it in your own voice.

## 0:00-0:45 - Show it working

- Open the public EC2 link in a browser.
- Add a sample task, refresh to show it persisted, complete it and delete it.
- Open the live /health endpoint and show its app/database status.
- Mention that this is a shared demo with sample data.

Explain: the task is inserted into SQLite and read back on the next page request.
The health endpoint actually queries the application table.

## 0:45-1:50 - Explain the diagram and choices

Show docs/architecture.svg or the rendered README.

Walk through browser -> internet gateway/public IP -> security group ->
Nginx on port 80 -> Gunicorn/Flask on loopback port 8000 ->
SQLite on encrypted EBS. Responses travel back through those layers.

Cover each required choice and an alternative:

| Choice you must explain | Main reason | Alternative and why you did not choose it |
| --- | --- | --- |
| t3.micro | Enough for this low-traffic app with a small memory footprint | t3.small has more headroom but costs/consumes credits faster |
| Amazon Linux 2023 | AWS-maintained image with systemd and SSM integration | Ubuntu is also valid; AL2023 keeps this setup close to AWS documentation |
| SQLite | Real persistence without operating another database service | RDS PostgreSQL improves managed backups/concurrency but adds cost and setup |
| Nginx and direct public IP | Small traffic path; app server stays private to the host | ALB is useful for multi-host traffic and TLS but adds resources |

Say what you gave up: one host is a single point of failure; SQLite and data
share the host's root volume; HTTP has no encryption in transit.

## 1:50-2:30 - Security, cost and the optional extra

Show the security group's inbound rule and the instance details.

- Only inbound TCP 80. No SSH or database port is exposed.
- Session Manager handles administration using an instance role.
- Gunicorn is non-root. The secret stays outside Git.
- Explain your actual account plan, credit coverage and cost budget.
- Identify the costs: instance hours, EBS storage, public IPv4 and eligible
  transfer. Do not say that a small instance alone guarantees a free bill.
- CloudFormation is the optional extra: it reproduces the network and host
  and waits for a successful readiness signal.

If showing Billing, avoid exposing personal details, account identifiers or
payment information in the recording. You can describe verified values instead.

## 2:30-3:10 - One real troubleshooting story

Use your incident log. State:

1. The symptom.
2. The checks or logs that narrowed it down.
3. The root cause.
4. The fix and verification.

Do not invent a deployment failure. If your deployment was smooth, you can
accurately discuss a local testing issue you actually reviewed and reproduced,
or a controlled failure exercise clearly labeled as an exercise.
The operations guide records the validation findings from this starter.
The assignment's strongest evidence will be an issue you can explain from
your own investigation.

## 3:10-3:45 - What changes before real users

Prioritize a few concrete improvements:

- HTTPS with a trusted certificate and secure session cookies.
- Login and per-user permissions, because the current board is shared.
- A managed database with tested backup/restore and a data migration plan.
- External uptime/disk alerts and tested automated deployments with rollback.
- Redundancy if customers need the service to survive a host failure.

Close by showing the repository README, deployment information and diagram.

## Record and submit

- Keep the final recording between 2 and 5 minutes.
- Check the app URL in a private browser window before recording.
- Verify that the repository and video are accessible to the reviewer.
- Replace every README TODO with a verified value or an honest status.
- Reply to the original assignment email with the live URL, repo URL and video.
- Leave the app running until MangoApps confirms review.

## Explain these without reading

- What is EC2, and why does this assignment require it?
- What does Nginx do that the Python application does not?
- Why is Gunicorn bound to 127.0.0.1 rather than 0.0.0.0?
- Where is the data? What survives a process restart? What loses the data?
- How does /health distinguish a database failure from a healthy app?
- Why does Session Manager work without an inbound SSH rule?
- Which resources consume credits, and what does a budget alert do?
- What does CloudFormation reproduce, and what does it not deploy on every push?
