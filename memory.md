# Project Memory: Region-Scoped Admin Hierarchy

This file serves as a reference for the recently implemented **Jurisdictional Admin Hierarchy & Region Scoping** feature. Use this document to quickly test the feature and understand the system architecture.

---

## 1. Feature Overview & Architecture

We extended the admin panel to support a cascading delegation flow:
`Super Admin` $\rightarrow$ `State Admin` $\rightarrow$ `District Admin`

### Role Privileges
*   **Super Admin:**
    *   Global visibility.
    *   Only role that can create and edit regions (states and districts).
    *   Can assign any administrative scope (Super, State, or District) to any user globally.
    *   Full access to the global impact dashboard.
*   **State Admin:**
    *   Visibility restricted to their assigned state.
    *   Can view and rename **districts within their own state only**.
    *   Can assign/delegate **District Admin** roles within their state.
    *   Cannot create regions, manage other states, or access the global impact dashboard.
*   **District Admin:**
    *   Visibility restricted to issues within their assigned district.
    *   No user-management or region-management capabilities at all.
    *   Cannot access the global impact dashboard.

---

## 2. Test Credentials

Use these pre-seeded accounts to verify the behavior of different scopes:

| Role | Email | Password | Scope / Region |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@communityhero.gov.in` | `adminpass` | Global |
| **State Admin** | `tamilnadu.admin@communityhero.gov.in` | `tnstatepass` | Tamil Nadu |
| **District Admin** | `chennai.admin@communityhero.gov.in` | `chennaipass` | Chennai, Tamil Nadu |

---

## 3. How to Run the Project

### Start the Backend
From the project root:
```powershell
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --reload
```

### Start the Frontend
From the project root:
```powershell
cd frontend
npm run dev
```

---

## 4. Manual Verification Steps

### Step 1: Super Admin Verification (Global Control)
1. Log in as `admin@communityhero.gov.in` (`adminpass`).
2. Verify you see the **DASHBOARD** link in the navbar and a gold **SUPER** badge next to your name.
3. Go to `/admin/regions`:
    * Verify all seeded states (Karnataka, Tamil Nadu, etc.) are visible.
    * Click **NEW REGION** and create a new state (e.g., Name: `Kerala`, Type: `State`).
    * Click **NEW REGION** again and create a district under it (e.g., Name: `Kochi`, Type: `District`, Parent State: `Kerala`).
    * Click the edit (pencil) icon next to `Kochi` and rename it to `Kochi City`. Click the **Check** icon to save.
4. Go to **ASSIGN ADMIN JURISDICTION**:
    * Select any citizen, set the scope to **State Admin**, select **Kerala**, and click **ASSIGN JURISDICTION** to promote them.

### Step 2: State Admin Verification (Scoped Scopes & Delegation)
1. Log in as `tamilnadu.admin@communityhero.gov.in` (`tnstatepass`).
2. Verify you see a blue **STATE** badge. The **DASHBOARD** link should be hidden.
3. Go to `/admin/regions`:
    * Verify you **only** see the *Tamil Nadu* card and its districts. *Karnataka* and *Kerala* must be hidden.
    * Verify the **NEW REGION** button is hidden.
    * Verify you can rename districts under Tamil Nadu, but cannot create or rename states.
4. Go to **ASSIGN ADMIN JURISDICTION**:
    * Select a user and verify you can only select the **District Admin** scope.
    * Verify the region dropdown only displays districts under Tamil Nadu (e.g., *Chennai*).

### Step 3: District Admin & Citizen Restrictions
1. Log in as `chennai.admin@communityhero.gov.in` (`chennaipass`).
2. Verify you see an emerald-green **DISTRICT** badge.
3. Try to navigate directly to `/admin/regions` or `/dashboard`. Verify you are redirected back with access denied.

---

## 5. Recent Fixes & Scoping Enhancements

1. **Leaderboard Scoping**: Scoped the leaderboard by state so that Citizens, District Admins, and State Admins only see rankings within their own state. Super Admins retain a global view.
2. **Explore Map & Issue Scoping**: Restricted the issues retrieved in the Explore Map. Citizens and District Admins only see issues in their district, State Admins only see issues in their state, and Super Admins see all issues globally.
3. **Pulsing User Location Marker**: Implemented a pulsing blue dot marker ("You are here") on the Explore Map using browser geolocation, allowing citizens to see their current location relative to reported issues.
4. **Session Geolocation & District Map Scoping**:
    *   **On Login/Session Init**: If a citizen, district admin, or state admin logs in (or loads the app), the application automatically requests their browser geolocation, calls the backend `PATCH /auth/me/location` endpoint to reverse-geocode their coordinates via Nominatim, and updates their profile with the resolved `state_id` and `region_id`.
    *   **District-Only Map View**: The Explore Map is centered and zoomed specifically to the user's district bounding box (for citizens and district admins) or state bounding box (for state admins), showing a dashed border outline. Issues on the map are filtered to their district/state.
    *   **Super Admin View**: Super Admins always default to a Delhi-centered map on load, but retain unrestricted global panning/scrolling and view all issues.
5. **Fix for Unlimited Likes / Upvotes**: Fixed a frontend bug where upvotes and verifications would increment the counter locally even if the backend rejected them as duplicates. Removed the optimistic increment on failure and added a clear error alert.
6. **Database Transaction Collision:** Fixed a bug in `assign_admin_region` (`admin.py`) where calling `async with db.begin():` crashed because the session had already started a transaction. Replaced it with direct property assignment followed by `await db.commit()`.
7. **Dropdown Visibility & UI Theme Alignments:** Fixed a CSS bug where select dropdown options had black text on a dark background. Restyled the dropdown to match the light theme (`var(--paper-bright)` background with `var(--ink)` text) and replaced all undefined CSS variables with correct theme tokens.
