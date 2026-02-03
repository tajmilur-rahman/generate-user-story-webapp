doc_text_raw = """

Erie Insurance Agents’ Handbook
Requirements Document
Prepared by: Tajmilur Rahman, PhD, Asst. Professor @ Gannon University
December 10th, 2023







Entities
Erie Insurance, Branch, Agency (Primary Agent), Sales Team, Producer, CSR, Account
Project Background
Erie Insurance is the primary entity. It has many branches. Each branch is located in different locations. 
Agency is another entity that works with a branch. Many agencies work with one branch. 
An agency has a primary agent, and many other agents who sell insurance products individually or as a “Sales” team. Within a sales team an agent can be a “Producer”, or a “CSR”. 
An agency is typically identified by the primary agent. Each agent including primary, individual, and agents working within a sales team has an unique ID and they are identified by this ID. 
The unique ID of an agent has the following format: AANNNN 
In this format, A - represents Alphabet, N - represents Number
The first two letters: “AA” represents the state
Agent has the following attributes: 
Agent ID
First Name
Middle Name
Last Name
Preferred Name
Account / Location / Address
Sales Team is a collection of:
Producers (composed of agents)
CSR (composed of agents)
Product is another entity which is sold by the agencies, or individual agents (sales, producers, CSRs) within an agency.
Project Description
Erie Insurance has 18 branches as of today. Each branch organizes their annual board meeting events where they celebrate their performance of the past year and distributes awards to the best performing agents or agencies. Thousands (2200) of agents/agencies (principal agents / executives) may participate in the Annual Board Meeting (ABM) of a branch. Currently the agency's information is shared via pdf or text documents where it takes a lot of manual effort to find out someone in particular in the document.

Erie Insurance needs a mobile application where all the agencies/agents will be accessible by a robust search functionality. The search functionality is the primary feature of this application where a person (agent) can be found by typing any text in the search text-field. 
Besides agent search, Erie Insurance also wants their users of this application to be able to browse and navigate to an event, browse and navigate to an agent manually through branches. 

Figure 1 (a) shows the landing frame of the iOS mobile application where there will be a search bar and two navigator panels i) events, ii) branches. The search bar will be a universal search element throughout the application. Users should be able use the search bar to search for an agent any time while using the app. When users tap on the Events panel, the panel will be expanded listing up all the events. When users tap on the Branches panel, the panel will be expanded listing up all the branches of Erie Insurance. 


		a				  b				     c
Figure 1: a) Landing Frame b) Tap on Events c) Tap on Branches
Project Specifications
Erie Insurance wants an iOS mobile application for V1.0 (MVP) and later on an Android version too.
Agent search is the primary feature of this application.
The search keywords from the search text-field will be looked into the Agent’s Name, Location, Phone Number, Email Address, Description (short bio), and all other information associated with an agent.
All users of the mobile app will have similar access levels and can perform the same functionalities.
Users should be able to browse events or branches from the landing frame. 
Users must login to the app. The Landing Frame in Figure 2 will be launched once the user is successfully logged in.
Each user will have a basic profile page containing a profile picture and other basic details such as affiliation, designation, ID number, location (city, state), fun-fact, hobbies, short bio.
EI Agents’ Handout - Minimum Viable Product (MVP) Requirements
Functional Requirements
Full-text Search: Users would like to type in any fragment of an agent’s name, designation, company, city, description/bio, hobbies, fun-facts, or anything else associated with the user. Search results will appear as a dropdown suggestions list. 
Login: Users must login to the app before he/she can do anything in the app.
If not registered in the app, a link/button will allow users to quickly signup in the app.
Login authentication has to be implemented via two-steps variations technique by sending a text/email to the user.
Once login is successful, the user will be taken to the landing screen (Figure 2 (a)).
Registration: Users must signup before using the app. 
Users can create a user account in the app using his/her Agent ID, email address, and password.
During app signup uploading a profile picture and providing other details is not mandatory. 
Once signup is completed the user will be taken to the login screen. 
Search
Search must be wildcard and full text.
Search results must be linked to user profiles.
Users will be able to type anything in the search text field.
The search keyword will be looked up into the following data in the following order:
First Name
Last Name
Middle Name
Preferred Name
Agency (affiliation)
Designation
Biography or description
Address
Fun-fact
For example: If a keyword typed in is “Thoma” then all agents having their first names starting with “Thoma” will appear first. After that if any agent has their last name starting with “Thoma” will be added in the search result. And so on for middle name, preferred name, agency name, designation, bio, address, and fun-fact. 
Figure 2 (a) shows a search UI mockup.
Profile Page of Agent:
Once a user taps on an agent listed in the search result drop-down list, the user will go to the profile page of the corresponding agent as shown in Figure 3 (b).
Navigate through Events: The landing page contains two panels, i) events and ii) branches. Users can navigate through the events. Once the user taps on the “Event” panel, the user will see the list of different types of events. This is just an expansion of the panel instead of going to a new frame/screen. Similarly, once a user taps on the Branches” panel, users will see the list of branches. 
If a user taps on an event type, for example “Annual Board Meeting”, then the user will be taken to the list of all ABMs sorted by date earliest first. From this screen the user will be able to tap on a particular ABM of a branch. User will then be taken to another screen where the following details will be accessible:
Event Details
Branch Info
Award Info
Reports
Figure 3 shows the event navigation screens.
Navigate through Branches (up to primary agent level): On the other hand, if the user taps on a Branch from the list of branches, for example “Raleigh” then the user will be taken to a screen where details of the Raleigh branch is accessible.
Branches
Agencies
Primary Agent
ID
Account/Location

		a 				     b
Figure 2: a) Agent Search b) User profile navigating from the search result


a			      b				   c

	         d				      e
Figure 3: Event navigation screens starting from a to e.
Non-functional Requirements
Not discussed
Deadlines
UAT & Training: March 1st, 2024
User Acceptance Testing
Data: 
 
V1.0 Release Date: April 10th, 2024
Success Criteria
– MVP v1.0 before April 2024’s (April 11) ABM event.
– At least the following features are completed 
o   Basic search capability – Full-text search
– MVP users are senior leaders
Post-MVP Requirements
Discussed but not confirmed
Mobile App
Connect (may be later)
Social media (may be later)
Gamification (may be later)
Badges
Milestones
Social networking (may be later)
Push notifications (may be later)

Web App / Admin Panel
Features
Users
Data operator
Super user
Use Case
Data Source
 
Server Infrastructure
Database
Web Server
   



"""

doc_text = """
        Entities
        Erie Insurance, Branch, Agency (Primary Agent), Sales Team, Producer, CSR, Account
        Project Background
    Erie Insurance is the primary entity. It has many branches. Each branch is located in different locations. 
    Agency is another entity that works with a branch. Many agencies work with one branch. 
    An agency has a primary agent, and many other agents who sell insurance products individually or as a “Sales” team. Within a sales team an agent can be a “Producer”, or a “CSR”. 
    An agency is typically identified by the primary agent. Each agent including primary, individual, and agents working within a sales team has an unique ID and they are identified by this ID. 
    The unique ID of an agent has the following format: AANNNN 
    In this format, A - represents Alphabet, N - represents Number
    The first two letters: “AA” represents the state
    Agent has the following attributes: 
    Agent ID
    First Name
    Middle Name
    Last Name
    Preferred Name
    Account / Location / Address
    Sales Team is a collection of:
    Producers (composed of agents)
    CSR (composed of agents)
    Product is another entity which is sold by the agencies, or individual agents (sales, producers, CSRs) within an agency.
    Project Description
    Erie Insurance has 18 branches as of today. Each branch organizes their annual board meeting events where they celebrate their performance of the past year and distributes awards to the best performing agents or agencies. Thousands (2200) of agents/agencies (principal agents / executives) may participate in the Annual Board Meeting (ABM) of a branch. Currently the agency's information is shared via pdf or text documents where it takes a lot of manual effort to find out someone in particular in the document.

    Erie Insurance needs a mobile application where all the agencies/agents will be accessible by a robust search functionality. The search functionality is the primary feature of this application where a person (agent) can be found by typing any text in the search text-field. 
    Besides agent search, Erie Insurance also wants their users of this application to be able to browse and navigate to an event, browse and navigate to an agent manually through branches. 

    Figure 1 (a) shows the landing frame of the iOS mobile application where there will be a search bar and two navigator panels i) events, ii) branches. The search bar will be a universal search element throughout the application. Users should be able use the search bar to search for an agent any time while using the app. When users tap on the Events panel, the panel will be expanded listing up all the events. When users tap on the Branches panel, the panel will be expanded listing up all the branches of Erie Insurance. 
    Project Specifications
    Erie Insurance wants an iOS mobile application for V1.0 (MVP) and later on an Android version too.
    Agent search is the primary feature of this application.
    The search keywords from the search text-field will be looked into the Agent’s Name, Location, Phone Number, Email Address, Description (short bio), and all other information associated with an agent.
    All users of the mobile app will have similar access levels and can perform the same functionalities.
    Users should be able to browse events or branches from the landing frame. 
    Users must login to the app. The Landing Frame in Figure 2 will be launched once the user is successfully logged in.
    Each user will have a basic profile page containing a profile picture and other basic details such as affiliation, designation, ID number, location (city, state), fun-fact, hobbies, short bio.
    EI Agents’ Handout - Minimum Viable Product (MVP) Requirements
    Functional Requirements
    Full-text Search: Users would like to type in any fragment of an agent’s name, designation, company, city, description/bio, hobbies, fun-facts, or anything else associated with the user. Search results will appear as a dropdown suggestions list. 
    Login: Users must login to the app before he/she can do anything in the app.
    If not registered in the app, a link/button will allow users to quickly signup in the app.
    Login authentication has to be implemented via two-steps variations technique by sending a text/email to the user.
    Once login is successful, the user will be taken to the landing screen (Figure 2 (a)).
    Registration: Users must signup before using the app. 
    Users can create a user account in the app using his/her Agent ID, email address, and password.
    During app signup uploading a profile picture and providing other details is not mandatory. 
    Once signup is completed the user will be taken to the login screen. 
    Search
    Search must be wildcard and full text.
    Search results must be linked to user profiles.
    Users will be able to type anything in the search text field.
    The search keyword will be looked up into the following data in the following order:
    First Name
    Last Name
    Middle Name
    Preferred Name
    Agency (affiliation)
    Designation
    Biography or description
    Address
    Fun-fact
    For example: If a keyword typed in is “Thoma” then all agents having their first names starting with “Thoma” will appear first. After that if any agent has their last name starting with “Thoma” will be added in the search result. And so on for middle name, preferred name, agency name, designation, bio, address, and fun-fact. 
    Figure 2 (a) shows a search UI mockup.
    Profile Page of Agent:
    Once a user taps on an agent listed in the search result drop-down list, the user will go to the profile page of the corresponding agent as shown in Figure 3 (b).
    Navigate through Events: The landing page contains two panels, i) events and ii) branches. Users can navigate through the events. Once the user taps on the “Event” panel, the user will see the list of different types of events. This is just an expansion of the panel instead of going to a new frame/screen. Similarly, once a user taps on the “Branches” panel, users will see the list of branches. 
    If a user taps on an event type, for example “Annual Board Meeting”, then the user will be taken to the list of all ABMs sorted by date earliest first. From this screen the user will be able to tap on a particular ABM of a branch. User will then be taken to another screen where the following details will be accessible:
    Event Details
    Branch Info
    Award Info
    Reports
    Navigate through Branches (up to primary agent level): On the other hand, if the user taps on a Branch from the list of branches, for example “Raleigh” then the user will be taken to a screen where details of the Raleigh branch is accessible.
    Branches
    Agencies
    Primary Agent
    ID
    Account/Location
    Non-functional Requirements
    Not discussed
    Deadlines
    UAT & Training: March 1st, 2024
    User Acceptance Testing
    Data: 
    V1.0 Release Date: April 10th, 2024
    Success Criteria
    – MVP v1.0 before April 2024’s (April 11) ABM event.
    – At least the following features are completed 
    o   Basic search capability – Full-text search
    – MVP users are senior leaders
    Post-MVP Requirements
    Discussed but not confirmed
    Mobile App
    Connect (may be later)
    Social media (may be later)
    Gamification (may be later)
    Badges
    Milestones
    Social networking (may be later)
    Push notifications (may be later)

    Web App / Admin Panel
    Features
    Users
    Data operator
    Super user
    Use Case
    Data Source
     
    Server Infrastructure
    Database
    Web Server
    """

refine_text="""

    Erie Insurance Agents’ Handbook
    Requirements Document
    Prepared by: Tajmilur Rahman, PhD, Assistant Professor at Gannon University
    December 10th, 2023

    Entities
    - Erie Insurance
    - Branch
    - Agency (Primary Agent)
    - Sales Team
    - Producer
    - CSR
    - Account

    Project Background
    Erie Insurance is the primary entity with multiple branches located in different locations. Each branch works with multiple agencies. An agency has a primary agent and other agents who sell insurance products individually or as part of a sales team. The agents are identified by a unique ID in the format AANNNN, where A represents an alphabet and N represents a number. The agents have various attributes such as ID, first name, middle name, last name, preferred name, and account/location/address. The sales team consists of producers and CSRs, both composed of agents. Products are sold by agencies or individual agents within an agency.

    Project Description
    Erie Insurance currently has 18 branches. Each branch organizes an annual board meeting event to celebrate their performance and distribute awards to the best performing agents or agencies. Thousands of agents/agencies may participate in the Annual Board Meeting (ABM) of a branch. Currently, agency information is shared via PDF or text documents, requiring manual effort to find specific information.

    Erie Insurance needs a mobile application that provides a robust search functionality to access all agencies/agents. The search functionality is the primary feature of this application, allowing users to find agents by typing any text in the search text field. Additionally, users should be able to browse and navigate to events and agents manually through branches.

    Figure 1:
    (a) Landing Frame
    (b) Tap on Events
    (c) Tap on Branches

    Project Specifications
    - Erie Insurance wants an iOS mobile application for V1.0 (MVP) and later an Android version.
    - Agent search is the primary feature of this application.
    - The search keywords will be looked into the agent's name, location, phone number, email address, description (short bio), and other associated information.
    - All users of the mobile app will have similar access levels and functionalities.
    - Users should be able to browse events or branches from the landing frame.
    - Users must log in to the app, and the landing frame will be launched after successful login.
    - Each user will have a basic profile page with a profile picture and other details such as affiliation, designation, ID number, location, fun fact, hobbies, and short bio.

    EI Agents’ Handout - Minimum Viable Product (MVP) Requirements
    Functional Requirements
    1. Full-text Search: Users can type any fragment of an agent's name, designation, company, city, description/bio, hobbies, fun facts, or any associated information. Search results will appear as a dropdown suggestions list.
    2. Login: Users must log in to the app before using it. If not registered, users can quickly sign up.
    3. Registration: Users must sign up before using the app. They can create an account using their Agent ID, email address, and password. Uploading a profile picture and providing other details is optional.
    4. Search:
       - Wildcard and full-text search.
       - Search results linked to user profiles.
       - Users can type anything in the search text field.
       - Search keywords will be looked up in the following data:
         - First Name
         - Last Name
         - Middle Name
         - Preferred Name
         - Agency (affiliation)
         - Designation
         - Biography or description
         - Address
         - Fun fact
    5. Profile Page of Agent: Tapping on an agent in the search result dropdown list will take the user to the agent's profile page.
    6. Navigate through Events: Users can navigate through events from the landing page. Tapping on the "Events" panel will expand the panel and display the list of different types of events.
    7. Navigate through Branches (up to primary agent level): Tapping on a branch from the list of branches will take the user to a screen with details of the branch, agencies, and primary agent.

    Non-functional Requirements
    Not discussed

    Deadlines
    - UAT & Training: March 1st, 2024
    - V1.0 Release Date: April 10th, 2024

    Success Criteria
    - MVP v1.0 to be completed before April 2024's ABM event.
    - Basic search capability (full-text search) should be implemented.

    Post-MVP Requirements
    Discussed but not confirmed
    - Mobile App Connect
    - Social media integration
    - Gamification (badges, milestones)
    - Social networking
    - Push notifications

    Web App / Admin Panel
    Features
    - Users
    - Data operator
    - Super user

    Use Case
    - Data Source

    Server Infrastructure
    - Database
    - Web Server
    """


expected_requirements_less = """
    Functional Requirements:
    1. Profile Page of Agent: When a user taps on an agent in the search results, they should be taken to the profile page of that agent.
    2. Navigate through Events: Users should be able to navigate through different types of events. Tapping on an event should display the details of that event.
    3. Navigate through Branches: Users should be able to navigate through different branches. Tapping on a branch should display the details of that branch, including the primary agent and account/location information.
    """

expected_requirements = """
    Functional Requirements:
    1. Full-text Search: Users should be able to search for agents by typing any fragment of their name, designation, company, city, description/bio, hobbies, or fun-facts.
    2. Login: Users must login to the app before accessing any features. Login authentication should be implemented using two-step verification.
    3. Registration: Users must sign up before using the app. They can create an account using their Agent ID, email address, and password.
    4. Search: The search functionality should be wildcard and full-text. The search results should be linked to user profiles. Users should be able to search by typing anything in the search text field.
    5. Profile Page of Agent: When a user taps on an agent in the search results, they should be taken to the profile page of that agent.
    6. Navigate through Events: Users should be able to navigate through different types of events. Tapping on an event should display the details of that event.
    7. Navigate through Branches: Users should be able to navigate through different branches. Tapping on a branch should display the details of that branch, including the primary agent and account/location information.
    """

expected_epics = """"{
Epics": [
        {
            "User Story": "Users should be able to search for agents by typing any fragment of their name, designation, company, city, description/bio, hobbies, or fun-facts.",
            "Deliverables": {
                "architecture_design": "Design of the search functionality module within the system.",
                "database_schema_design": "Database schema design for storing agent information and enabling efficient search functionality.",
                "unit_tests": "Unit tests for the search functionality to ensure accurate search results.",
                "user_training_documentation": "Documentation on how users can effectively utilize the search feature.",
                "production_support_plan": "Plan for providing support and maintenance for the search feature in the production environment."
            }
        },
        {
            "User Story": "Users must login to the app before accessing any features. Login authentication should be implemented using two-step verification.",
            "Deliverables": {
                "architecture_design": "Design of the authentication module with two-step verification.",
                "database_schema_design": "Database schema design for storing user account information securely.",
                "unit_tests": "Unit tests for the authentication process to ensure secure login functionality.",
                "user_training_documentation": "Documentation on how users can create an account and login securely.",
                "production_support_plan": "Plan for providing support and maintenance for the authentication system in the production environment."
            }
        },
        {
            "User Story": "When a user taps on an agent in the search results, they should be taken to the profile page of that agent.",
            "Deliverables": {
                "architecture_design": "Design of the profile page module to display agent information.",
                "database_schema_design": "Database schema design for storing detailed agent profiles.",
                "unit_tests": "Unit tests for the profile page functionality to ensure correct display of agent information.",
                "user_training_documentation": "Documentation on how users can view agent profiles and navigate through them.",
                "production_support_plan": "Plan for providing support and maintenance for the profile page feature in the production environment."
            }
        },
        {
            "User Story": "Users should be able to navigate through different types of events. Tapping on an event should display the details of that event.",
            "Deliverables": {
                "architecture_design": "Design of the events navigation module to categorize and display event details.",
                "database_schema_design": "Database schema design for storing event information and linking it to the navigation feature.",
                "unit_tests": "Unit tests for the events navigation functionality to ensure proper event display.",
                "user_training_documentation": "Documentation on how users can explore and view event details.",
                "production_support_plan": "Plan for providing support and maintenance for the events navigation in the production environment."
            }
        },
        {
            "User Story": "Users should be able to navigate through different branches. Tapping on a branch should display the details of that branch.",
            "Deliverables": {
                "architecture_design": "Design of the branches navigation module to categorize and display branch details.",
                "database_schema_design": "Database schema design for storing branch information and linking it to the navigation feature.",
                "unit_tests": "Unit tests for the branches navigation functionality to ensure accurate branch details display.",
                "user_training_documentation": "Documentation on how users can navigate through branches and view branch details.",
                "production_support_plan": "Plan for providing support and maintenance for the branches navigation in the production environment."
            }
        },
        {
            "User Story": "Integration Test",
            "Deliverables": {
                "test_plan_design": "Design of the integration test plan to validate the interaction between different modules.",
                "implementation": "Implementation of the integration tests to ensure seamless functionality across the system."
            }
        }
    ]
}
"""
