# 🤖 TagDebt Bot

## Introduction
TagDebt automates the labeling of GitHub issues using machine learning. It identifies **Self-Admitted Technical Debt (SATD)**, assigns labels, and notifies contributors.

For technical details and deployment strategies, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Quick Start
1.  **GitHub App**: Place your `bot_key.pem` in `/Bot`.
2.  **Configuration**: Create `config.json` in both `/Bot` and `/ModelsBackend` by copying the respective `config.json.example` files and customizing them.
3.  **Secrets**: Create `Bot/bot_email.secret` with the email address on the 1st line and the app password on the 2nd.
4.  **Model Data**: (If using local Li 2022 model) Download [weight files](https://zenodo.org/records/7821209) to `ModelsBackend/plugins/satd_li_2022/data/`. Rename them to `embeddings.bin` and `weights.hdf5`.
5.  **Launch**:
    ```bash
    docker compose up
    ```
6.  **Webhooks**: Start Smee to forward webhooks:
    ```bash
    smee --url https://smee.io/Wpx6fSOaWjEaOK --path /webhook --port 5001
    ```

## Usage
- `/tdbot label`: Classifies the issue.
- `/tdbot label <name>`: Manually applies a label.
- `/tdbot help`: Shows usage details.

## Configuration
Edit `Bot/config.json`. Key options include:
- `payload-type`: What to analyze ("title", "description", "merged", "both").
- `endpoint`: Backend URL (e.g., `http://model:8000/models/Model1_IssueTracker_Li2022_ESEM`).
- `auto-label`: Enable auto-processing (true/false).
- `send-emails`: Toggle notifications (true/false).

### Example `config.json`
```json
{
  "payload-type": "description",
  "endpoint": "http://model:8000/models/Model1_IssueTracker_Li2022_ESEM",
  "label-location": "label",
  "auto-label": false,
  "send-emails": true,
  "email-info": {
    "which-labels": "specific",
    "specific-labels": ["SATD"],
    "recipients" : ["dev@example.com"]
  }
}
```
For a full list of configuration keys and email placeholders, see [ARCHITECTURE.md#detailed-configuration-reference](ARCHITECTURE.md#detailed-configuration-reference).

---

## License
MIT License - see [LICENSE](LICENSE).

## Acknowledgments
Special thanks to all contributors and maintainers. The Deep Learning SATD detection logic is based on research by Yikun Li, Mohamed Soliman, and Paris Avgeriou.

## Contact
For questions or feedback, please open an issue in the GitHub repository.
