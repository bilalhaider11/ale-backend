# OAuth Setup Guide

This guide explains how to configure **Google** and **Microsoft** OAuth for the Ale Homecare application across local, development, test, and production environments. Follow the steps carefully to ensure both backend and frontend are correctly configured.

---

## Google OAuth Setup

1. **Create a Project**
   - Go to the **Google Cloud Console**.
   - Create a project named `ale-homecare`.

2. **Enable and Configure OAuth**
   - Navigate to **APIs & Services → Credentials**.
   - Click **Create Credentials → OAuth client ID**.
   - If prompted, configure the **OAuth consent screen**.

3. **OAuth Client ID Configuration**
   - **Application Type:** Web application  
   - **Name:** Ale Homecare
   - **Authorized JavaScript Origins:**
     - Local: `http://localhost:9000`
     - Development: `https://alehealthdev.com`
     - Test: `https://test.alehealth.com`
     - Production: `https://alehealth.com`
   - **Authorized Redirect URIs:**
     - Local: `http://localhost:9000/auth/callback`
     - Development: `https://alehealthdev.com/auth/callback`
     - Test: `https://test.alehealth.com/auth/callback`
     - Production: `https://alehealth.com/auth/callback`

4. **Save Credentials**
   - Save the **Client ID** and **Client Secret** in `.env.secrets` as:
     ```
     GOOGLE_CLIENT_ID=<your_client_id>
     GOOGLE_CLIENT_SECRET=<your_client_secret>
     ```
   - In the frontend application, set:
     ```
     VUE_APP_GOOGLE_CLIENT_ID=<your_client_id>
     ```

---

## Microsoft OAuth Setup

1. **Create an App Registration**
   - Go to the **Azure Portal**.
   - Navigate to **App registrations → New registration**.
   - **Name:** Ale Homecare `<Environment: Optional>`
   - **Supported Account Types:**  
     Accounts in any organizational directory (Any Microsoft Entra ID tenant – Multitenant) and personal Microsoft accounts (e.g., Skype, Xbox).

2. **Redirect URIs**
   - Local: `http://localhost:9000/auth/callback`
   - Development: `https://alehealthdev.com/auth/callback`
   - Test: `https://test.alehealth.com/auth/callback`
   - Production: `https://alehealth.com/auth/callback`

3. **Generate Client Secret**
   - Go to **Manage → Certificates & Secrets**.
   - Click **New Client Secret**.
   - **Name:** Ale Homecare `<Environment: Optional>`
   - Copy the **Secret Value** immediately (it will be hidden later).
   - From the app registration **Overview**, copy the **Application (client) ID**.

4. **Save Credentials**
   - Save the **Client ID** and **Client Secret** in `.env.secrets` as:
     ```
     MICROSOFT_CLIENT_ID=<your_client_id>
     MICROSOFT_CLIENT_SECRET=<your_client_secret>
     ```
   - In the frontend application, set:
     ```
     VUE_APP_MICROSOFT_CLIENT_ID=<your_client_id>
     ```
