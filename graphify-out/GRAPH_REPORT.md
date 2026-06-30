# Graph Report - CN Hackathon  (2026-06-30)

## Corpus Check
- 101 files · ~40,860 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 575 nodes · 964 edges · 41 communities (38 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 126 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1660e04c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]

## God Nodes (most connected - your core abstractions)
1. `User` - 56 edges
2. `useApp()` - 20 edges
3. `IssueRepository` - 18 edges
4. `Issue` - 15 edges
5. `InMemoryCache` - 14 edges
6. `Base` - 13 edges
7. `safe_transaction()` - 11 edges
8. `get_leaderboard_route()` - 11 edges
9. `admin_update_issue()` - 10 edges
10. `build_issue_response()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `get_current_user()` --calls--> `decode_access_token()`  [INFERRED]
  backend/app/core/dependencies.py → backend/app/core/security.py
- `get_current_user_optional()` --calls--> `decode_access_token()`  [INFERRED]
  backend/app/core/dependencies.py → backend/app/core/security.py
- `resolve_admin_region_ids()` --calls--> `get_district_ids_for_state()`  [INFERRED]
  backend/app/routers/dashboard.py → backend/app/core/dependencies.py
- `list_departments()` --calls--> `get_district_ids_for_state()`  [INFERRED]
  backend/app/routers/departments.py → backend/app/core/dependencies.py
- `IssueService` --uses--> `UnauthorizedActionException`  [INFERRED]
  backend/app/services/issue_service.py → backend/app/core/exceptions.py

## Import Cycles
- None detected.

## Communities (41 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (65): assert_admin_can_access_issue(), assert_admin_can_touch_department(), can_assign(), ensure_not_last_super_admin(), get_current_user(), get_current_user_optional(), get_district_ids_for_state(), get_scope_filter() (+57 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (47): get_me(), login(), AsyncSession, Register a new citizen user and return a JWT access token., Authenticate user credentials and return a JWT access token., Get profile information for the currently authenticated user., Set or update the authenticated user's state., Resolve coordinates to state/district regions and update the user's location pro (+39 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (21): DuplicateIssueException, NagarikException, Raised when a user attempts an action they are not permitted to do., Raised when a duplicate issue action/submission is detected., Base exception for all domain errors in Nagarik., UnauthorizedActionException, create_access_token(), decode_access_token() (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (27): HotspotMap, MunicipalAnalyticsPage(), DepartmentsPage(), AdminLayout(), ManageIssuesPage(), RegionManagementPage(), UserDirectoryPage(), AuthCallbackHandler() (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (16): Badge, Base, Comment, IssueFollower, Issue, Region, StatusHistory, Verification (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (32): build_admin_issue_response(), Helper to populate verification and comment counts on IssueResponse for admin vi, build_issue_response(), create_comment(), create_issue(), follow_issue(), get_comments(), get_issue() (+24 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (26): dependencies, clsx, framer-motion, leaflet, lucide-react, next, react, react-dom (+18 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (26): create_app(), lifespan(), google_callback(), google_login(), AsyncSession, Request, get_dashboard_hotspots(), get_department_rankings() (+18 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (6): InMemoryCache, Any, Find and delete keys matching a pattern., Fallback in-memory cache when Redis is unavailable., Wrapper that tries connecting to Redis, otherwise falls back to InMemoryCache., RedisCacheWrapper

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (9): Department, DepartmentRepository, AsyncSession, UUID, DashboardService, AsyncSession, UUID, Fetch overall civic impact stats. Cached in Redis (2m TTL). (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (15): fetch_region_geometry(), find_nearby_issues(), get_bbox_filter(), get_or_create_region(), AsyncSession, UUID, Resolve the administrative region (state + district) for a coordinate via Nomina, Reverse geocode latitude and longitude to a human-readable address using OSM Nom (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.21
Nodes (15): _call_groq_api(), categorize_issue_text_only(), categorize_issue_vision(), check_duplicate_ai(), Any, AsyncSession, UUID, Main pipeline for categorization with caching and two-stage fallback. (+7 more)

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (10): UserBadge, GamificationService, AsyncSession, BackgroundTasks, UUID, Background task to verify badge conditions and award them in a transaction., Increment user points in DB and trigger badge check & leaderboard cache invalida, Verify criteria and award new badges. Expected to run inside a transaction. (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (5): archivo, ibmPlexMono, ibmPlexSans, metadata, WORDS

### Community 14 - "Community 14"
Cohesion: 0.24
Nodes (7): Notification, NotificationService, AsyncSession, UUID, Send an email using Resend, or fallback to logging., Create an in-app notification in the database., Fetch issue details and notify the reporter and all followers in-app + email. Ru

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (20): IssueNotFoundException, Raised when an issue is not found in the system., get_db(), AsyncSession, Context manager to run database operations safely inside a transaction.     If a, safe_transaction(), IssueService, AsyncSession (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.20
Nodes (8): Run migrations in 'offline' mode., Run migrations in 'online' mode., run_migrations_offline(), run_migrations_online(), add_tracing_ctx(), Automatically append tracing variables from ContextVars to all structured logs., Setup structlog configuration., setup_logging()

### Community 17 - "Community 17"
Cohesion: 0.38
Nodes (3): GlassmorphismNavBar(), Component(), cn()

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (3): Settings, BaseSettings, eslintConfig

### Community 19 - "Community 19"
Cohesion: 0.40
Nodes (4): HotspotService, AsyncSession, UUID, Fetch issue coordinates via repository and run DBSCAN clustering. Cached in Redi

### Community 20 - "Community 20"
Cohesion: 0.50
Nodes (3): compilerOptions, paths, @/*

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (12): 1. Feature Overview & Architecture, 2. Test Credentials, 3. How to Run the Project, 4. Manual Verification Steps, 5. Recent Fixes & Scoping Enhancements, Project Memory: Region-Scoped Admin Hierarchy, Role Privileges, Start the Backend (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.46
Nodes (3): AsyncSession, UUID, UserRepository

### Community 38 - "Community 38"
Cohesion: 0.50
Nodes (3): Deploy on Vercel, Getting Started, Learn More

## Knowledge Gaps
- **55 isolated node(s):** `Config`, `Config`, `Config`, `Config`, `Config` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Community 0` to `Community 1`, `Community 2`, `Community 4`, `Community 5`, `Community 37`, `Community 7`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.225) - this node is a cross-community bridge._
- **Why does `Issue` connect `Community 4` to `Community 5`, `Community 9`, `Community 10`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Base` connect `Community 4` to `Community 0`, `Community 9`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `User` (e.g. with `Base` and `UserRepository`) actually correct?**
  _`User` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `useApp()` (e.g. with `MunicipalAnalyticsPage()` and `DepartmentsPage()`) actually correct?**
  _`useApp()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `IssueRepository` (e.g. with `Comment` and `Issue`) actually correct?**
  _`IssueRepository` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Run migrations in 'offline' mode.`, `Run migrations in 'online' mode.`, `FastAPI Dependency to retrieve the authenticated user from the JWT token.` to the rest of the system?**
  _151 weakly-connected nodes found - possible documentation gaps or missing edges._