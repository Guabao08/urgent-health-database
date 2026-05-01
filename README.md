# VitalTriage

A real-time priority-based triage dashboard for health lines. It utilizes a **4-ary Max-Heap** to automatically surface the highest-urgency cases and features a sleek, responsive UI to display active priority queues to medical staff.

The application is built with a **Stateless Python FastAPI** backend and a **React/Vite** frontend, making it fully ready for serverless deployment on Vercel.

## Vercel Deployment Guide

To deploy this full-stack application (Python Backend + Vite Frontend) onto Vercel, follow these step-by-step instructions:

### 1. Set Up Supabase (Database)
Vercel's serverless architecture requires a persistent database (you can't store state in memory).
1. Go to [Supabase](https://supabase.com/) and create a new project.
2. Navigate to the **SQL Editor** in your Supabase dashboard and run this command to create the required table:
   ```sql
   CREATE TABLE patients (
       id bigint primary key,
       name text not null,
       priority int not null,
       symptoms text not null,
       status text default 'active',
       timestamp bigint not null
   );
   ```
3. Go to **Project Settings -> API** and copy your `Project URL` and `anon public` API Key. You will need these for Vercel!

### 2. Install Vercel CLI (Optional but recommended)
If you don't want to use the Vercel website, you can use their command line tool.
Open your terminal and run:
```bash
npm i -g vercel
```

### 3. Deploy to Vercel
1. Open your terminal in the root directory of this project (`/Users/andygu/Urgent Health Database`).
2. Run the deployment command:
   ```bash
   vercel
   ```
3. You will be prompted with a few questions:
   - *Set up and deploy?* **Y**
   - *Which scope?* **(Select your Vercel account)**
   - *Link to existing project?* **N**
   - *What's your project's name?* **vital-triage** (or whatever you prefer)
   - *In which directory is your code located?* **./** (Just press Enter)
   - *Want to override the settings?* **N** (Vercel will automatically read the `vercel.json` we created!)

### 4. Add Environment Variables
Once Vercel uploads your code, it will give you a **Production URL**, but it won't be fully working until you add your Supabase credentials!
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard) and click on your newly deployed project.
2. Navigate to **Settings -> Environment Variables**.
3. Add the following two variables:
   - Key: `SUPABASE_URL` | Value: *(Paste your Supabase Project URL)*
   - Key: `SUPABASE_KEY` | Value: *(Paste your Supabase anon public key)*
4. Click **Save**.

### 5. Re-deploy (to apply variables)
Because environment variables are baked in during the build process or applied to fresh instances, navigate to the **Deployments** tab in Vercel, click the three dots (`...`) next to your most recent deployment, and hit **Redeploy**.

🎉 **You're Done!** Visit your Vercel production URL and your Priority Triage app is live!

---

## Local Development
To run this project locally:

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
