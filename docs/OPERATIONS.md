# Operations and troubleshooting

Use these commands in **EC2 > Connect > Session Manager**.
The instance uses Amazon Linux 2023. Do not open SSH just to read logs.

## Inspect before changing

```bash
sudo systemctl status mango-todo --no-pager
sudo systemctl status nginx --no-pager
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1/health
sudo ss -ltnp
sudo journalctl -u mango-todo -n 100 --no-pager
sudo tail -n 100 /var/log/nginx/error.log
sudo tail -n 100 /var/log/cloud-init-output.log
```

The first curl tests Gunicorn directly. The second includes Nginx.
Compare them before changing security groups.

| Symptom | Investigate | Appropriate response |
| --- | --- | --- |
| Stack fails before an instance exists | CloudFormation Events, IAM permissions, quota, AMI and instance availability | Correct the specific failed resource; do not create repeated stacks |
| No readiness signal | cloud-init-output.log, outbound internet path, package or GitHub download | Correct bootstrap failure; readiness should not be bypassed |
| Repository not found | Repository visibility, OWNER/REPOSITORY and top-level project layout | Use a public repo with app.py and deploy/ at its root |
| Git fetch fails | Commit SHA and repository membership | Copy the full commit SHA from the correct repository |
| Public connection times out | Public IP, subnet route, internet gateway, inbound port 80 and Nginx listener | Fix the failed network layer; do not expose every port |
| Nginx returns 502 | Direct Gunicorn curl, systemd logs, port 8000, SELinux audit if enforcing | Fix service startup or proxy access; do not disable SELinux |
| /health returns 503 | App logs, data directory permissions, schema and disk space | Fix the database cause; do not replace the health response with a static success |
| Form returns 400 after restart | Refresh the page; inspect cookies and token handling | Local sessions can expire; production secret must persist |
| Session Manager is unavailable | SSM agent, attached instance profile, Region and outbound HTTPS | Check amazon-ssm-agent and role attachment; allow initial registration time |
| New code does not appear | Running checkout SHA and EC2 first-boot behavior | Use the update procedure below; changing user data alone does not redeploy |

For disk and permissions:

```bash
df -h
sudo ls -ld /var/lib/mango-todo
sudo ls -l /var/lib/mango-todo
sudo systemctl status amazon-ssm-agent --no-pager
```

The data directory should belong to `mangoapp`; the application files belong
to root and are readable by the service. Do not solve a permissions error with
`chmod 777`. Do not paste the environment file or secrets into your incident log.

If stack creation failed and you chose to preserve resources, the instance may
still be available for inspection. Delete that failed stack after collecting the
needed evidence, before starting a replacement. If you allowed rollback, the
failed instance and its local logs may already be gone.

## Restart and verify persistence

Create a sample task in the public app, then:

```bash
sudo systemctl restart mango-todo
curl -i --retry 10 --retry-connrefused --retry-delay 1 http://127.0.0.1/health
```

Refresh the browser. The task should still exist.
Both services are enabled at boot. An OS reboot has a short availability gap.
Do not stop or terminate the host while the reviewer still needs the link.
An EC2 stop/start can change its automatically assigned public IP.
After any stop/start, get the current IP from EC2 and update your submitted link.

## Apply a small code update on the existing host

This version has infrastructure as code, but no automatic deployment pipeline.
Push/upload the new files to GitHub and copy the new full commit SHA.
For small updates that do not require schema migration:

```bash
sudo git -C /opt/mango-source rev-parse HEAD
```

Record that previous SHA for rollback, then substitute the real new SHA:

```bash
TASKBOARD_COMMIT='REPLACE_WITH_NEW_40_CHARACTER_SHA'
sudo git -C /opt/mango-source fetch --depth 1 origin "$TASKBOARD_COMMIT"
sudo git -C /opt/mango-source checkout --detach FETCH_HEAD
sudo bash /opt/mango-source/deploy/provision.sh
curl -i http://127.0.0.1/health
```

Recheck the public URL and a saved task. Provisioning preserves the data
directory and existing secret. It restarts services, so a short outage is expected.
For rollback, repeat with the recorded previous SHA. A code rollback does not
undo a database schema change; design and test migrations separately.
Record the current deployed commit in README.

Changing the CloudFormation GitCommit parameter is not enough: EC2 user data
normally runs only on first boot. Replacing the instance recreates the database
in this design, so do not treat host replacement as a data-preserving update.

## Back up SQLite correctly

For sample data this is optional. For data you need to preserve, use SQLite's
backup API, which is safe with a live WAL database:

```bash
sudo /opt/mango-todo/venv/bin/python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

backup_dir = Path("/var/backups/mango-todo")
backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
target_path = backup_dir / f"tasks-{stamp}.sqlite3"
source = sqlite3.connect("file:/var/lib/mango-todo/tasks.sqlite3?mode=ro", uri=True)
target = sqlite3.connect(target_path)
try:
    source.backup(target)
finally:
    target.close()
    source.close()
target_path.chmod(0o600)
print(target_path)
PY
```

This backup is still on the same root EBS volume. It is not disaster recovery.
Copy any important backup to separate protected storage before deleting or
replacing the host. Test restoration separately. Do not commit database files.

## Keep an honest incident log

Record a real issue you investigate while running or deploying the app:

| Question | Your observation |
| --- | --- |
| What failed, and where? | TODO |
| What did the user or health check show? | TODO |
| What were your first two checks? | TODO |
| Which log line or test identified the root cause? | TODO |
| What did you change? | TODO |
| How did you verify recovery and avoid recurrence? | TODO |

An actual issue found while validating this starter: a non-ASCII CSRF token
triggered `TypeError` in Python's string form of `hmac.compare_digest`.
The fix compares UTF-8 bytes, and
`test_malformed_unicode_csrf_token_returns_400` now verifies rejection with
HTTP 400. Review the code and run the test to understand it. This was a local
validation finding with AI assistance, not an incident observed on your AWS host.

The local Gunicorn run also logged a control-socket permission error in the
restricted validation environment. The unused control interface is explicitly
disabled with `--no-control-socket`; systemd manages the service instead.
Do not claim either of these happened during your own AWS deployment unless
you observed it there.

## After MangoApps confirms review

1. Save any needed data and observations first.
2. Delete the `mangoapps-devops` stack in CloudFormation.
3. Wait for `DELETE_COMPLETE`. Investigate `DELETE_FAILED` instead of assuming cleanup.
4. Verify the instance is terminated and its EBS root volume is deleted.
5. Delete any other failed or test stacks you created; inspect Billing for
   unrelated leftover resources in every Region you used.

The supplied template deletes its root EBS volume on termination, including
the app database. Deleting the stack is irreversible for that data without a backup.
Keep the account budget alerts while you still have AWS resources.
