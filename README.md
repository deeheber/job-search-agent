# Job Search Agent

**🔍 Your AI job hunting sidekick** - Drop in a company name, get the inside scoop on who's hiring.

No more endless scrolling through job boards or wondering if that dream company has openings. This agent does the detective work for you, surfacing real opportunities with position details and direct application links. Built on AWS with all the enterprise bells and whistles, but simple enough to get running in minutes.

## What's Inside

🎯 **Smart job hunting** - Company hiring status with all the juicy details  
🌐 **Multi-source magic** - Scrapes career pages and taps job board APIs  
🏗️ **Production-ready setup** - CDK infrastructure that just works  
🧪 **Local testing** - Try before you deploy  
🚀 **Auto-deploy pipeline** - Push code, get infrastructure  
📊 **Full observability** - See what's happening under the hood

## Right Now

- **Company lookup**: Toss in a company name, get their hiring pulse
- **Live data**: Fresh intel from job boards and career pages
- **Smart parsing**: AI extracts the good stuff - titles, links, dates
- **Timestamp magic**: Know when jobs were posted and data was fetched

## Coming Soon

- **Set it and forget it**: Scheduled checks via EventBridge
- **Instant alerts**: Get pinged when opportunities pop up

## The Stack

Python handles the agent smarts, TypeScript manages the infrastructure. Why? Because [Strands](https://strandsagents.com) + Python = 🔥 for AI agents, and [AWS CDK](https://aws.amazon.com/cdk/) + TypeScript = 🔥 for cloud infrastructure. Best tools for each job.

## Get Started

```bash
# Try it locally first
cd agent && source .venv/bin/activate && python src/agentcore_app.py

# Test with: {"company": "Panic Inc.", "title": "Software Engineer"}

# Deploy to AWS when ready
aws configure && cd cdk && npm install && npm run build && cdk deploy
```

**Ready to hunt?** Get your job search agent running on AWS in under 10 minutes. ⚡️

Check [DEPLOYMENT.md](DEPLOYMENT.md) for the full setup walkthrough.
