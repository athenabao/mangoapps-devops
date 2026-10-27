# Start here

Work through one phase at a time. You do not need Docker, Terraform, a custom
domain, AWS CLI credentials or an AWS access key for this version.
This starter supplies the code and documentation. Your live AWS link,
GitHub repository and video still need to be created.

## 1. Prepare your accounts and budget

1. Create or sign in to your account at https://aws.amazon.com/free/.
2. For a new account, use the free plan offered by AWS. Check the account's
   actual service eligibility, credit balance and expiration. If you already
   had an AWS account, do not assume it qualifies for new-customer credits.
3. Turn on MFA for the root account. Use an authorized administrator console
   login for this deployment; keep root access for initial account tasks.
   See [AWS account setup guidance](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct.html).
   Do not create or share AWS access keys for this walkthrough.
4. Choose one Region, such as **US West (Oregon), us-west-2**, and use it for
   CloudFormation, EC2 and Systems Manager. Check that t3.micro is available
   and covered by your plan/credits in that Region.
5. In **Billing and Cost Management > Budgets**, create a small monthly cost
   budget, for example USD 5, with actual-cost and forecast email alerts.
   Check whether credits are included in the calculation. Excluding credits
   helps you see usage that is consuming them. If email verification is
   requested, complete it. Budget alerts are not a hard spending cap.
6. Sign in to https://github.com or create a free account.

Do not launch extra resources from other tutorials. This project creates its
own small VPC and EC2 host. The app must remain live until the reviewer finishes.

**Checkpoint:** You can open AWS Billing, see your plan/credits, and see your budget.

## 2. Run the app on your computer

Unzip the project and open Terminal. Change to the folder that contains
`app.py`. If it is in Downloads:

```bash
cd ~/Downloads/mangoapps-devops-starter
python3 --version
```

Use Python 3.11 or newer. If needed, install it from
https://www.python.org/downloads/ and reopen Terminal. Then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m flask --app app:create_app run --host 127.0.0.1 --port 5050
```

Open http://127.0.0.1:5050 in your browser. Add a task, refresh the page,
complete it and delete it. Open http://127.0.0.1:5050/health.
Stop the server with Ctrl+C. Restart it and verify any remaining tasks persist.
The local secret may rotate on restart, so refresh before submitting another form.
The production deployment uses a persistent secret.

**Checkpoint:** Tests pass; the app and health page work locally.

## 3. Put the project on GitHub

Use a **public** repository, for example `mangoapps-devops`. This deployment
fetches public code; it never needs a GitHub password or token on EC2.

You can upload through GitHub's website:

1. Create a public repository. Initialize it with a README if the site requires
   an initial file; you will replace it with the README from this package.
2. Choose **Add file > Upload files**.
3. Upload the project files and folders into the **root** of the repository:
   `app.py`, `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`,
   `README.md`, `START_HERE.md`, `.gitignore`, `templates/`, `static/`,
   `deploy/`, `docs/` and `tests/`.
4. On macOS, Cmd+Shift+. reveals hidden files such as `.gitignore`.
   Select only the files listed above. Do not upload `.venv/`, `instance/`,
   `__pycache__/`, database files, keys or passwords.
5. Commit the upload. The repository homepage should show `app.py` directly;
   it should not be inside an extra `mangoapps-devops-starter/` folder.
6. Click the latest commit and copy its **full 40-character SHA**.
7. Write down your repository as `YOUR_USERNAME/mangoapps-devops`.
   Open the repository in a private browser window to confirm it is public.

If you already use Git, pushing the project is also fine. Review `git status`
before committing; the included ignore file excludes local data and secrets.

**Checkpoint:** The public repo contains app.py and deploy/ at its top level.

## 4. Create the AWS deployment

CloudFormation is AWS's infrastructure-as-code service. The template describes
the host and network, so you can reproduce and explain the setup.

1. Open **CloudFormation** in the Region you selected.
2. Choose **Create stack > With new resources (standard)**.
3. Under the template source, choose **Upload a template file**.
4. Upload `deploy/cloudformation.yaml` from the unzipped project.
5. Name the stack `mangoapps-devops`.
6. Set the parameters:

   | Parameter | Value |
   | --- | --- |
   | GitHubRepository | Your actual OWNER/REPOSITORY, without https:// or .git |
   | GitCommit | The full SHA you copied |
   | InstanceType | Leave t3.micro |
   | LatestAmiId | Leave the supplied Amazon Linux parameter |

7. Keep the other stack settings at their defaults. Review the IAM capability
   acknowledgment: the template creates the role that lets Session Manager
   administer this instance. It is not an administrator role.
8. On the final review page, select **Preserve successfully provisioned resources**
   as the stack-failure option if available. This leaves a failed host available
   for log inspection. It also means failed resources must be cleaned up manually.
9. Review the template's resources and your cost coverage. Then create the stack.
10. Watch **Events**. Bootstrap can take several minutes; the readiness timeout is
    20 minutes. Success should end in `CREATE_COMPLETE`, not merely an EC2
    instance showing `running`.
11. Open **Outputs**, then copy and open `AppUrl` and `HealthUrl`.
    Use the explicit `http://` links. HTTPS is not configured in this starter.

If the stack fails, inspect Events and [docs/OPERATIONS.md](docs/OPERATIONS.md).
Do not keep launching more stacks; preserved failed hosts can also consume credits.

**Checkpoint:** Someone outside your computer can open the app and its health URL.

## 5. Verify the live deployment

1. Add two sample tasks in a private browser window. Refresh and confirm them.
2. Complete one task and delete the other.
3. Open the live health link and confirm it says `healthy`.
4. In **EC2 > Instances**, select the instance ID from CloudFormation Outputs.
5. Choose **Connect > Session Manager > Connect**. Allow a few minutes for initial
   agent registration if the instance is new.
6. In that shell:

```bash
sudo systemctl status mango-todo --no-pager
sudo systemctl status nginx --no-pager
curl -i http://127.0.0.1/health
sudo ss -ltnp
```

Nginx should listen publicly on port 80. Gunicorn should listen on
`127.0.0.1:8000`. There should be no public database listener.

7. With a task still saved, restart the app:

```bash
sudo systemctl restart mango-todo
curl -i --retry 10 --retry-connrefused --retry-delay 1 http://127.0.0.1/health
```

8. Refresh the public page. Confirm the task survived the restart.
9. Check **EC2 > Security groups > Inbound rules**: only TCP 80 is needed.
10. Return to Billing. Confirm your credit balance and the budget you configured.
11. Fill in the deployment table in README, and record what you tested.

**Checkpoint:** The live app, persistence, health, administration and cost checks pass.

## 6. Record and submit

Use [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for a 3-4 minute outline.
Explain your actual choices and show actual results. Keep passwords, billing
details, account identifiers and terminal environment files out of the recording.

The assignment asks for:

- Your live AWS app link.
- Your Git repository link, with the README and diagram.
- A 2-5 minute demo video link.

You can host the recording on Loom or as an unlisted YouTube video.
Check that another person can open all three links.
Reply to the original assignment email yourself after reviewing the submission.

Leave the EC2 app running until MangoApps confirms review. Only then follow
the cleanup instructions. If AWS credits are close to expiring before review,
address that before the live app becomes unavailable.
