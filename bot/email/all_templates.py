
from typing import List, Dict, Any

def get_complete_template_collection() -> List[Dict[str, Any]]:
    
    templates = []
    
    templates.extend([
        {
            'category': 'judges',
            'name': 'initial-invite',
            'subject': 'Judge Invitation: {event_name} - {date}',
            'body': '''Dear {name},

We would be honored to have you serve as a judge for {event_name}, taking place on {date} at {location}.

As a respected expert in your field, your insights would be invaluable in evaluating the innovative projects our participants will create. The event will feature multiple tracks with a total prize pool of {prize_pool}.

Event Details:
• Date: {date}
• Location: {location}
• Duration: {duration}
• Judging Time: 4-6 hours

We will provide meals, networking opportunities, and recognition as an official judge.

Please let us know if you're available by replying to {contact_email}.

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'judges',
            'name': 'follow-up',
            'subject': 'Follow-up: Judge Invitation for {event_name}',
            'body': '''Hi {name},

Following up on our invitation for you to judge {event_name} on {date}.

We'd love your expertise to help evaluate the amazing projects our participants will build. The time commitment is just {duration}.

Questions about the format or logistics? Contact me at {contact_email}.

Would you be interested in joining us as a judge?

Best regards,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'judges',
            'name': 'confirmation',
            'subject': 'Confirmed: Judge Details for {event_name}',
            'body': '''Dear {name},

Thank you for confirming your participation as a judge for {event_name}!

Event Details:
• Date: {date}
• Time: {time}
• Location: {location}
• Check-in: 30 minutes before judging
• Duration: {duration}

What to Expect:
• Welcome meal with other judges
• Brief orientation on judging criteria
• Project demonstrations (5-7 minutes each)
• Deliberation session
• Awards ceremony

We'll send the detailed judging rubric 24 hours before the event.

Looking forward to seeing you at {event_name}!

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'judges',
            'name': 'eb1-o1-angle',
            'subject': 'Judging Opportunity: Strengthen Your EB-1/O-1 Profile',
            'body': '''Dear {name},

We'd like to invite you to judge {event_name}, an opportunity that could strengthen your EB-1 or O-1 visa application profile.

As a judge, you would:
• Demonstrate sustained acclaim in your field
• Show evidence of evaluating others' work
• Build documentation of community contributions
• Network with distinguished professionals

This provides concrete evidence of extraordinary ability - key for EB-1A or O-1 applications.

Event: {date} at {location}
Time Commitment: {duration}

We'll provide a detailed recommendation letter for your immigration attorney.

Interested? Reply to {contact_email}.

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'judges',
            'name': 'thank-you',
            'subject': 'Thank You for Judging {event_name}!',
            'body': '''Dear {name},

Thank you for being an outstanding judge at {event_name}! Your expertise was invaluable.

Event Highlights:
• {participants} participants
• Incredible projects and innovations
• Your feedback inspired many developers

We've prepared:
• Official judge certificate (attached)
• Event photos
• Summary of winning projects

We hope you enjoyed the experience and would love to have you back for future events!

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'judges',
            'name': 'future-collab',
            'subject': 'Future Collaboration Opportunities',
            'body': '''Hi {name},

It was fantastic having you as a judge at {event_name}! We'd love to explore more collaboration opportunities.

Upcoming Opportunities:
• Mentor for our next hackathon
• Speaker for our tech talk series
• Advisory board member
• Workshop facilitator

Would any of these interest you? Let's schedule a brief call to discuss.

Contact me at {contact_email}.

Looking forward to continuing our partnership!

Best regards,
{organization} Team''',
            'tone': 'casual'
        }
    ])
    
    templates.extend([
        {
            'category': 'sponsors',
            'name': 'first-touch',
            'subject': 'Partnership Opportunity: {event_name}',
            'body': '''Dear {name},

I'm reaching out to explore a partnership opportunity for {event_name}, taking place on {date} at {location}.

This {duration} hackathon brings together {participants} talented developers and designers, focusing on {theme}.

Why Partner With Us:
• Direct access to pre-screened talent
• Brand exposure to engaged tech community
• Recruitment and networking opportunities
• Showcase innovation leadership

Sponsorship Benefits:
• Logo placement on all materials
• Booth space for representation
• Speaking opportunities
• Access to participant information
• Social media promotion

We have several tiers starting at ${min_sponsorship}. I'd love to discuss a package that aligns with your goals.

Available for a call this week? Contact me at {contact_email}.

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'sponsors',
            'name': 'follow-up',
            'subject': 'Re: Partnership Opportunity - {event_name}',
            'body': '''Hi {name},

Following up on sponsoring {event_name} on {date}.

Quick recap:
• {participants} talented developers
• Focus: {theme}
• Sponsorship: Starting at ${min_sponsorship}

Previous sponsors found great value in recruiting talent and building brand awareness.

Available for a 15-minute call this week?

Best regards,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'sponsors',
            'name': 'package-details',
            'subject': '{event_name} Sponsorship Packages',
            'body': '''Dear {name},

Thank you for your interest in sponsoring {event_name}!

SPONSORSHIP TIERS:

🥇 TITLE SPONSOR - ${title_amount}
• Event naming rights
• Premium booth location
• 10-minute keynote slot
• Logo on all materials
• Access to all participant resumes

🥈 PLATINUM - ${platinum_amount}
• Prominent logo placement
• Premium booth space
• 5-minute speaking opportunity
• Access to participant contacts

🥉 GOLD - ${gold_amount}
• Logo on materials and website
• Standard booth space
• Networking session access

All packages include professional photography and post-event reports.

Which package interests you? Contact me at {contact_email}.

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'sponsors',
            'name': 'discount-custom-deal',
            'subject': 'Special Offer: Custom {event_name} Package',
            'body': '''Hi {name},

Since we're {weeks_until} weeks from {event_name}, I can offer a custom sponsorship package with excellent value.

CUSTOM PACKAGE:
• Investment: ${custom_amount} (20% off standard)
• Logo on all materials
• Booth space for 2 representatives
• 3-minute speaking opportunity
• Access to participant resumes
• Social media promotion

This package normally costs ${original_amount}, available for ${custom_amount} if you confirm by {deadline}.

Interested? Reply or call {phone}.

Best regards,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'sponsors',
            'name': 'closing',
            'subject': 'Final Call: {event_name} - {days_left} Days Left',
            'body': '''Dear {name},

With {days_left} days until {event_name}, this is the final sponsorship opportunity.

Event Status:
• {participants} registered (sold out!)
• Amazing {theme} projects expected
• {judges} expert judges confirmed
• Significant media coverage planned

Last-Minute Package Available:
• Investment: ${last_minute_amount}
• Logo on event materials
• Booth space
• Networking access
• Post-event report

Please confirm by {final_deadline}. Contact me at {contact_email}.

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'sponsors',
            'name': 'payment-reminder',
            'subject': 'Payment Reminder: {event_name} Sponsorship',
            'body': '''Hi {name},

Friendly reminder that your sponsorship payment of ${amount} is due by {payment_deadline}.

Payment Details:
• Package: {package_type}
• Amount: ${amount}
• Invoice
• Due Date: {payment_deadline}

Payment options and details are in your original invoice.

Questions? Contact me at {contact_email}.

Thank you for your partnership!

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'sponsors',
            'name': 'thank-you',
            'subject': 'Thank You for Sponsoring {event_name}!',
            'body': '''Dear {name},

Thank you for being a fantastic sponsor of {event_name}!

Event Highlights:
• {participants} participants
• {projects} innovative projects
• {social_media_reach} social media impressions

Your Impact:
• {booth_visitors} booth visitors
• {social_mentions} social media mentions
• Positive participant feedback
• Great recruitment opportunities

Attached:
• Professional event photos
• Detailed metrics report
• Interested participant contacts

We'd love to have you back for future events!

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'sponsors',
            'name': 're-engagement',
            'subject': 'We Miss You! New Partnership Opportunities',
            'body': '''Hi {name},

It's been a while since {company} sponsored our events, and we miss having you!

Since our last collaboration:
• Hosted {events_since} successful events
• Engaged {participants_total} developers
• Expanded to {new_locations} locations

Upcoming Opportunities:
• {next_event}: {next_event_date}
• Monthly tech talks
• University partnerships
• Innovation challenges

We'd love to discuss new ways to collaborate. Available for a call?

Contact me at {contact_email}.

Looking forward to reconnecting!

Best regards,
{organization} Team''',
            'tone': 'casual'
        }
    ])
    
    templates.extend([
        {
            'category': 'participants',
            'name': 'confirmation',
            'subject': 'You\'re Registered for {event_name}!',
            'body': '''Hi {name},

Welcome to {event_name}! We're excited to have you join us on {date}.

Event Details:
• Date: {date}
• Time: {time}
• Location: {location}
• Duration: {duration}

What to Bring:
• Laptop and charger
• Government-issued ID
• Enthusiasm and creativity

What We Provide:
• Free meals and snacks
• Mentorship and support
• Prizes and recognition
• Networking opportunities

Check-in starts at {checkin_time}. Can't wait to see what you build!

Questions? Email {contact_email}.

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'participants',
            'name': 'pre-event-reminder',
            'subject': '{event_name} is Tomorrow - Final Details!',
            'body': '''Hi {name},

{event_name} is tomorrow! Here are the final details:

📍 Location: {location}
🕐 Check-in: {checkin_time}
🕑 Start: {start_time}
🕕 End: {end_time}

Don't Forget:
• Laptop and charger
• Government-issued ID
• Comfortable clothes

Schedule:
• Opening: {opening_time}
• Lunch: {lunch_time}
• Submissions: {submission_time}
• Closing: {closing_time}

Parking: {parking_info}
WiFi: {wifi_info}

See you tomorrow!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'participants',
            'name': 'kickoff',
            'subject': '{event_name} Starts Now - Let\'s Build!',
            'body': '''Hi {name},

{event_name} is officially underway! 🚀

Quick Reminders:
• Project submission deadline: {submission_time}
• Mentors available throughout the event
• Meals: {meal_times}
• WiFi: {wifi_info}

Resources:
• API documentation: {api_docs}
• Design assets: {design_assets}
• Help desk: {help_location}

Remember: Focus on building something you're passionate about. The judges love creativity and innovation!

Good luck and have fun!

Best,
{organization} Team''',
            'tone': 'hype'
        },
        {
            'category': 'participants',
            'name': 'mid-event-update',
            'subject': 'Halfway There! {event_name} Update',
            'body': '''Hi {name},

We're halfway through {event_name} and the energy is incredible!

⏰ Time Check:
• Current time: {current_time}
• Submission deadline: {submission_time}
• Time remaining: {time_remaining}

🍕 Upcoming:
• Dinner: {dinner_time}
• Late-night snacks: {snack_time}
• Mentor office hours: Ongoing

💡 Pro Tips:
• Start preparing your presentation
• Test your project thoroughly
• Don't forget to submit on time!

Keep building amazing things!

Best,
{organization} Team''',
            'tone': 'hype'
        },
        {
            'category': 'participants',
            'name': 'deadline-reminder',
            'subject': '⏰ 2 Hours Left - {event_name} Submission Deadline',
            'body': '''Hi {name},

Only 2 hours left until the {event_name} submission deadline!

⏰ IMPORTANT TIMES:
• Submission deadline: {submission_time}
• Presentation prep: {prep_time}
• Judging begins: {judging_time}

📝 SUBMISSION CHECKLIST:
□ Project uploaded to {submission_platform}
□ Demo video recorded (optional but recommended)
□ Team information complete
□ Project description written

🎯 PRESENTATION TIPS:
• Keep it under 3 minutes
• Focus on the problem you solved
• Show your working demo
• Explain your technical approach

Need help with submission? Find us at {help_location}.

You've got this! Finish strong!

Best,
{organization} Team''',
            'tone': 'hype'
        },
        {
            'category': 'participants',
            'name': 'closing',
            'subject': 'Amazing Work at {event_name}!',
            'body': '''Hi {name},

What an incredible {duration} at {event_name}! You should be proud of what you accomplished.

🎉 Event Wrap-up:
• {total_projects} projects submitted
• Amazing creativity and innovation
• Great collaboration and learning
• Fantastic presentations

🏆 Results announced at: {results_time}
📸 Photos will be available at: {photos_url}
🤝 Stay connected: {community_link}

Whether you win or not, you've gained valuable experience and made great connections.

Thank you for being part of {event_name}!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'participants',
            'name': 'results',
            'subject': '{event_name} Results - Congratulations!',
            'body': '''Hi {name},

The results are in! Congratulations to all participants of {event_name}.

🏆 WINNERS:
• 1st Place: {first_place}
• 2nd Place: {second_place}
• 3rd Place: {third_place}
• Special Awards: {special_awards}

Every project was impressive and showed incredible creativity!

📱 What's Next:
• Project showcase: {showcase_url}
• Photos: {photos_url}
• Community: {community_link}
• Newsletter: {newsletter_link}

🎯 Opportunities:
• Job/internship connections
• Future event invitations
• Mentorship programs
• Startup resources

Thank you for making {event_name} unforgettable!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'participants',
            'name': 'future-invites',
            'subject': 'You\'re Invited: Upcoming Events from {organization}',
            'body': '''Hi {name},

Hope you're still riding the high from {event_name}! We have exciting upcoming events you might enjoy.

🗓️ UPCOMING EVENTS:
• {next_event}: {next_date}
• Monthly meetup: {meetup_date}
• Workshop series: {workshop_date}
• Annual conference: {conference_date}

🎯 OPPORTUNITIES:
• Mentorship programs
• Startup incubator
• Job placement assistance
• Speaking opportunities

As a {event_name} alum, you get:
• Early registration access
• Alumni discount codes
• Priority mentorship matching
• Exclusive networking events

Stay connected:
• Community: {community_link}
• Newsletter: {newsletter_link}
• Social: {social_media}

Looking forward to seeing you at future events!

Best,
{organization} Team''',
            'tone': 'casual'
        }
    ])

    templates.extend([
        {
            'category': 'schools',
            'name': 'partnership-inquiry',
            'subject': 'STEM Partnership Opportunity: {event_name}',
            'body': '''Dear {school_name} Administration,

We're excited to explore a partnership opportunity between {organization} and {school_name} for our upcoming {event_name}.

EVENT OVERVIEW:
• Date: {date}
• Format: {duration} virtual/in-person hackathon
• Participants: High school students grades {grades}
• Focus: {theme} with {tracks} tracks

PARTNERSHIP BENEFITS:
• Expose students to real-world tech challenges
• Build coding and problem-solving skills
• Connect with industry professionals
• Certificate of participation for all students
• Potential scholarships and internships

We can customize the event to align with your curriculum and schedule.

Would you be interested in discussing this opportunity? Contact me at {contact_email}.

Best regards,
{organization} Team
Education Partnership Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'schools',
            'name': 'student-recruitment',
            'subject': 'Invitation: {school_name} Students to {event_name}',
            'body': '''Dear {school_name} Students,

We're thrilled to invite {school_name} students to participate in {event_name}, a premier hackathon designed for young innovators!

EVENT DETAILS:
• Date: {date}
• Location: {location} (virtual option available)
• Duration: {duration}
• Team Size: {team_size} students
• No coding experience required!

WHAT YOU'LL GAIN:
• Hands-on coding experience
• Mentorship from industry experts
• Networking with peers and professionals
• Prizes and recognition
• Portfolio-worthy projects

Registration deadline: {deadline}
Register at: {registration_link}

Questions? Email {contact_email}

We can't wait to see your innovative solutions!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'schools',
            'name': 'workshop-offer',
            'subject': 'Free Coding Workshop Series for {school_name}',
            'body': '''Dear {school_name} Faculty,

{organization} would like to offer a free coding workshop series for your students!

WORKSHOP DETAILS:
• Duration: {workshop_duration} (4-6 sessions)
• Topics: {workshop_topics}
• Format: Hands-on, project-based learning
• Materials: All provided by us
• Schedule: Flexible to fit your curriculum

BENEFITS:
• Introduce students to programming concepts
• Build computational thinking skills
• Prepare students for future STEM opportunities
• No cost to your school
• Professional instructor-led sessions

This aligns perfectly with {curriculum_standards} standards.

Interested? Let's schedule a planning call at {contact_email}.

Best regards,
{organization} Team
Education Programs Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'schools',
            'name': 'competition-results',
            'subject': '{school_name} Students Excel at {event_name}!',
            'body': '''Dear {school_name} Administration,

Congratulations! Your students made an outstanding showing at {event_name}!

RESULTS:
• {school_name} participants: {student_count}
• Top performers: {top_students}
• Winning projects: {winning_projects}
• Special recognitions: {special_awards}

STUDENT ACHIEVEMENTS:
• {achievement_highlights}
• Skills demonstrated: {skills_learned}
• Projects created: {project_count}

We're impressed by the creativity and technical skills your students brought to the competition.

Attached: Detailed results and student certificates

We'd love to continue our partnership for future events!

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'schools',
            'name': 'follow-up-partnership',
            'subject': 'Follow-up: Partnership Discussion for {event_name}',
            'body': '''Hi {contact_name},

Following up on our discussion about {school_name} participating in {event_name}.

QUICK RECAP:
• Event: {date} at {location}
• Student participation: Grades {grades}
• Partnership benefits: {benefits_summary}

NEXT STEPS:
• Schedule planning meeting
• Review curriculum alignment
• Discuss logistics and requirements
• Set registration timeline

I'm available for a call this week to finalize details.

Contact me at {contact_email} or {phone}.

Looking forward to working with {school_name}!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'schools',
            'name': 'thank-you-partnership',
            'subject': 'Thank You for Partnering with Us!',
            'body': '''Dear {school_name} Team,

Thank you for partnering with {organization} for {event_name}!

PARTNERSHIP HIGHLIGHTS:
• Students participated: {student_count}
• Projects completed: {project_count}
• Skills developed: {skills_list}
• Overall experience: {feedback_summary}

IMPACT ON STUDENTS:
• {impact_highlights}
• Future opportunities: {future_opportunities}

We've attached:
• Student certificates
• Project showcase photos
• Detailed participation report
• Future partnership opportunities

We'd love to continue this successful collaboration!

Best regards,
{organization} Team''',
            'tone': 'formal'
        }
    ])

    templates.extend([
        {
            'category': 'college-clubs',
            'name': 'club-invitation',
            'subject': 'Exclusive Invitation: {college_name} Clubs to {event_name}',
            'body': '''Dear {club_name} Leadership,

We're excited to invite {college_name} student clubs to participate in {event_name}!

EVENT OVERVIEW:
• Date: {date}
• Location: {location}
• Format: {duration} intensive hackathon
• Focus: {theme}

WHY PARTICIPATE:
• Showcase your club's talent
• Network with industry professionals
• Win prizes and recognition
• Build your club's reputation
• Gain valuable experience

SPECIAL CLUB BENEFITS:
• Team registration discount
• Club promotion on our platforms
• Leadership networking opportunities
• Potential sponsorship opportunities

Registration deadline: {deadline}
Register at: {registration_link}

Questions? Contact {contact_email}

We can't wait to see what {club_name} creates!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'college-clubs',
            'name': 'collaboration-proposal',
            'subject': 'Collaboration Proposal: {organization} x {college_name} Clubs',
            'body': '''Dear {club_name} President,

{organization} would like to propose a collaboration between our organizations!

COLLABORATION IDEAS:
• Joint hackathon events
• Workshop co-hosting
• Mentorship programs
• Internship pipelines
• Speaker series

POTENTIAL BENEFITS:
• Enhanced learning opportunities for students
• Industry connections for clubs
• Event promotion and reach
• Shared resources and expertise

We're particularly interested in collaborating on:
• {specific_interests}
• {collaboration_focus}

Would you be interested in exploring these opportunities?

Let's schedule a call to discuss: {contact_email}

Best regards,
{organization} Team
Partnerships Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'college-clubs',
            'name': 'club-challenge',
            'subject': 'Special Challenge for {college_name} Clubs!',
            'body': '''Hey {club_name} Team!

We've created a special challenge just for {college_name} clubs!

CHALLENGE DETAILS:
• Theme: {challenge_theme}
• Duration: {challenge_duration}
• Prize Pool: ${prize_amount}
• Eligibility: {college_name} students only

WHY JOIN:
• Win exclusive prizes
• Represent your college
• Build your club's portfolio
• Network with other clubs
• Gain industry recognition

RULES:
• {team_size} members per team
• {submission_requirements}
• Judging criteria: {criteria}

Deadline: {deadline}
Submit at: {submission_link}

Questions? Hit us up at {contact_email}

Good luck, {club_name}!

Best,
{organization} Team''',
            'tone': 'hype'
        },
        {
            'category': 'college-clubs',
            'name': 'club-success-story',
            'subject': '{club_name} Success Story from {event_name}!',
            'body': '''Dear {club_name} Leadership,

What an incredible performance by {club_name} at {event_name}!

ACHIEVEMENTS:
• Projects submitted: {project_count}
• Awards won: {awards_list}
• Special recognitions: {recognitions}
• Community impact: {impact}

TEAM HIGHLIGHTS:
• {team_achievements}
• Skills demonstrated: {skills}
• Innovation level: {innovation_rating}

We're proud to have {club_name} as part of our community!

Attached: Success story write-up for your club's promotion

We'd love to feature {club_name} in our newsletter and social media.

Congratulations again!

Best,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'college-clubs',
            'name': 'club-networking',
            'subject': 'Club Leaders Networking Event',
            'body': '''Hi {club_name} President,

We're hosting a special networking event for club leaders!

EVENT DETAILS:
• Date: {date}
• Time: {time}
• Location: {location}
• Format: {duration} networking session

WHAT TO EXPECT:
• Connect with other club leaders
• Learn from successful clubs
• Industry professional speakers
• Best practices sharing
• Collaboration opportunities

AGENDA:
• Welcome and introductions
• Success story presentations
• Industry insights
• Networking breakout
• Next steps discussion

This is a great opportunity to build relationships with other clubs and industry professionals.

RSVP by {rsvp_deadline} at {contact_email}

See you there!

Best,
{organization} Team''',
            'tone': 'casual'
        }
    ])

    templates.extend([
        {
            'category': 'communities',
            'name': 'community-partnership',
            'subject': 'Community Partnership: {organization} x {community_name}',
            'body': '''Dear {community_name} Leadership,

{organization} is excited to explore a partnership with {community_name}!

PARTNERSHIP OPPORTUNITIES:
• Joint community events
• Technology education programs
• Mentorship initiatives
• Local talent development
• Community challenge events

HOW WE CAN HELP:
• Provide technical expertise
• Offer event hosting support
• Share best practices
• Connect with industry partners
• Support local innovation

We're particularly interested in:
• {community_interests}
• {collaboration_areas}

This partnership could bring significant value to {community_name} members.

Would you be interested in discussing this further?

Contact me at {contact_email} to schedule a call.

Best regards,
{organization} Team
Community Partnerships Director''',
            'tone': 'formal'
        },
        {
            'category': 'communities',
            'name': 'community-event-invite',
            'subject': 'Exclusive Community Event: {event_name}',
            'body': '''Dear {community_name} Community,

You're invited to an exclusive community-focused {event_name}!

EVENT DETAILS:
• Date: {date}
• Location: {location}
• Format: {duration} community hackathon
• Focus: {community_theme}

WHY ATTEND:
• Solve real community challenges
• Connect with local innovators
• Learn new technologies
• Network with community leaders
• Win prizes for community impact

SPECIAL COMMUNITY BENEFITS:
• Local challenge focus
• Community leader mentorship
• Local business partnerships
• Community recognition
• Potential funding opportunities

Registration: {registration_link}
Deadline: {deadline}

Questions? Email {contact_email}

We look forward to seeing {community_name} at {event_name}!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'communities',
            'name': 'community-outreach',
            'subject': 'Technology Education for {community_name}',
            'body': '''Dear {community_name} Members,

{organization} wants to support technology education in your community!

PROGRAM OFFERINGS:
• Free coding workshops
• Tech career guidance
• Mentorship matching
• Internship opportunities
• Community tech events

WHAT WE PROVIDE:
• Professional instructors
• Curriculum materials
• Equipment and resources
• Certificates of completion
• Ongoing support

TARGET AUDIENCE:
• {target_demographics}
• {skill_levels}
• {age_groups}

This program is designed to bring technology education opportunities to {community_name}.

Interested in bringing this to your community?

Contact {contact_email} to learn more.

Best regards,
{organization} Team
Community Education Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'communities',
            'name': 'community-success',
            'subject': '{community_name} Makes Waves at {event_name}!',
            'body': '''Dear {community_name} Community,

What an amazing showing by {community_name} at {event_name}!

COMMUNITY ACHIEVEMENTS:
• Participants: {participant_count}
• Projects: {project_count}
• Awards: {awards_won}
• Community impact: {impact_level}

SUCCESS STORIES:
• {success_highlights}
• {community_benefits}
• {future_opportunities}

We're proud of the innovation and collaboration {community_name} brought to the event!

Attached: Community success report and photos

We'd love to continue supporting {community_name}'s growth!

Best,
{organization} Team''',
            'tone': 'casual'
        }
    ])

    templates.extend([
        {
            'category': 'mentors-speakers',
            'name': 'mentor-invitation',
            'subject': 'Mentor Invitation: Share Your Expertise at {event_name}',
            'body': '''Dear {name},

We're seeking experienced professionals like you to mentor participants at {event_name}!

MENTORING OPPORTUNITIES:
• One-on-one technical guidance
• Team project reviews
• Career advice sessions
• Industry insights sharing

EVENT DETAILS:
• Date: {date}
• Duration: {duration}
• Participants: {participant_count}
• Format: {event_format}

WHY MENTOR:
• Give back to the community
• Discover emerging talent
• Network with industry peers
• Enhance your leadership skills
• Build your professional network

TIME COMMITMENT:
• {time_commitment}
• Flexible scheduling
• Virtual option available

Interested? We'd love to have you as a mentor!

Contact {contact_email} to discuss availability.

Best regards,
{organization} Team
Mentorship Program Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'mentors-speakers',
            'name': 'speaker-invitation',
            'subject': 'Speaking Opportunity: {event_name} Keynote',
            'body': '''Dear {name},

We're honored to invite you to speak at {event_name}!

SPEAKING OPPORTUNITIES:
• Keynote presentation ({keynote_duration})
• Workshop session ({workshop_duration})
• Panel discussion participation
• Networking sessions

AUDIENCE:
• {participant_count} attendees
• {participant_types}
• {experience_levels}

TOPIC SUGGESTIONS:
• {suggested_topics}
• Industry trends and insights
• Career advice and guidance
• Technical deep-dives

WHY SPEAK:
• Reach engaged audience
• Share your expertise
• Build professional network
• Give back to the community

We're flexible with format and timing.

Would you be interested in speaking?

Contact {contact_email} to discuss possibilities.

Best regards,
{organization} Team
Speaker Relations Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'mentors-speakers',
            'name': 'workshop-facilitator',
            'subject': 'Workshop Facilitator: {workshop_topic} at {event_name}',
            'body': '''Hi {name},

We're looking for expert facilitators for our {workshop_topic} workshop at {event_name}!

WORKSHOP DETAILS:
• Topic: {workshop_topic}
• Duration: {workshop_duration}
• Audience: {participant_level}
• Format: {workshop_format}

WHAT WE NEED:
• Deep expertise in {topic_area}
• Teaching/facilitation experience
• Engaging presentation style
• Ability to adapt to audience needs

WHAT WE PROVIDE:
• Professional facilitation guide
• Technical support
• Audience management
• Honorarium compensation
• Travel arrangements (if applicable)

This is a great opportunity to share your knowledge with motivated learners!

Interested? Let's discuss the details.

Contact me at {contact_email}.

Best,
{organization} Team
Workshop Program Manager''',
            'tone': 'casual'
        },
        {
            'category': 'mentors-speakers',
            'name': 'thank-you-mentor',
            'subject': 'Thank You for Being a Mentor at {event_name}!',
            'body': '''Dear {name},

Thank you for being an outstanding mentor at {event_name}!

YOUR IMPACT:
• Teams mentored: {teams_mentored}
• Participants helped: {participants_helped}
• Hours contributed: {hours_contributed}
• Feedback received: {feedback_summary}

PARTICIPANT FEEDBACK:
• "{participant_feedback}"
• "{impact_quotes}"

We're continually impressed by mentors like you who generously share their expertise.

Attached: Mentor appreciation certificate

We'd love to have you back for future events!

Best regards,
{organization} Team''',
            'tone': 'formal'
        },
        {
            'category': 'mentors-speakers',
            'name': 'future-opportunities',
            'subject': 'Future Speaking and Mentoring Opportunities',
            'body': '''Hi {name},

Hope you're enjoying the post-{event_name} glow! We're already planning future events and would love your continued involvement.

UPCOMING OPPORTUNITIES:
• {next_event}: {next_date} - {next_role}
• Monthly workshop series
• Online mentorship program
• Industry panel discussions
• Guest lecture opportunities

WAYS TO STAY INVOLVED:
• Regular mentoring sessions
• Guest speaking engagements
• Workshop facilitation
• Advisory board participation
• Community leadership

Your expertise is invaluable to our community.

Interested in any of these opportunities?

Let's stay in touch: {contact_email}

Best,
{organization} Team''',
            'tone': 'casual'
        }
    ])

    templates.extend([
        {
            'category': 'press-media',
            'name': 'press-release',
            'subject': 'Press Release: {event_name} - {event_highlight}',
            'body': '''FOR IMMEDIATE RELEASE

{organization} Announces {event_name}

{location} - {date_description}

{organization} is excited to announce {event_name}, bringing together {participant_count} innovators for {duration} of intensive collaboration and creativity.

EVENT HIGHLIGHTS:
• {participant_count} participants from {regions}
• Focus on {theme} with {tracks} tracks
• Prize pool of ${prize_amount}
• {judge_count} expert judges from leading companies

WHAT TO EXPECT:
• Groundbreaking technological innovations
• Solutions to real-world challenges
• Networking opportunities with industry leaders
• Recognition for outstanding achievements

QUOTES:
"{quote_from_organizer}"
- {organizer_name}, {organizer_title}

For more information:
{contact_name}
{contact_title}
{contact_email}
{contact_phone}

About {organization}:
{organization_description}

Media Contact:
{contact_name}
{contact_email}
{contact_phone}

--- END ---''',
            'tone': 'formal'
        },
        {
            'category': 'press-media',
            'name': 'media-invitation',
            'subject': 'Media Invitation: {event_name} Press Conference',
            'body': '''MEDIA ADVISORY

{organization} Invites Media to {event_name}

WHAT: Press conference and media preview of {event_name}
WHEN: {date} at {time}
WHERE: {location}
WHY: {event_description}

EVENT DETAILS:
• {participant_count} participants competing
• {duration} intensive innovation challenge
• Focus on {theme}
• Prize pool: ${prize_amount}

MEDIA OPPORTUNITIES:
• Press conference with organizers
• Participant interviews
• Project demonstrations
• Networking with industry leaders
• Photo and video opportunities

RSVP REQUIRED
Contact: {contact_name}
Email: {contact_email}
Phone: {contact_phone}

We look forward to having you cover this exciting event!

Best regards,
{organization} Team
Media Relations Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'press-media',
            'name': 'interview-request',
            'subject': 'Interview Request: {interview_topic} for {event_name}',
            'body': '''Dear {journalist_name},

I'm reaching out from {organization} about an interview opportunity related to {event_name}.

INTERVIEW TOPIC:
{interview_topic}

WHY THIS MATTERS:
{topic_importance}

WHAT WE CAN DISCUSS:
• {discussion_points}
• Industry trends and insights
• Community impact and outcomes
• Future of innovation and technology

AVAILABILITY:
• {available_times}
• {interview_format} format preferred
• {location} location

We're excited about the potential coverage of {event_name} and believe this would be valuable content for your audience.

Would you be interested in scheduling an interview?

Contact me at {contact_email} or {phone}.

Best regards,
{organization} Team
Media Relations Coordinator''',
            'tone': 'formal'
        },
        {
            'category': 'press-media',
            'name': 'event-coverage-followup',
            'subject': 'Thank You for Covering {event_name}!',
            'body': '''Dear {journalist_name},

Thank you for the excellent coverage of {event_name}!

COVERAGE HIGHLIGHTS:
• {publication_name} article: "{article_title}"
• Reach: {impressions} impressions
• Engagement: {engagement_metrics}
• Community impact: {community_reach}

EVENT SUCCESS METRICS:
• {participant_count} participants
• {project_count} projects submitted
• {award_count} awards presented
• {media_outlets} media outlets covered

We're thrilled with how you captured the energy and innovation of the event.

Attached: High-resolution photos and additional content

We'd love to continue our media partnership for future events.

Best regards,
{organization} Team
Media Relations Coordinator''',
            'tone': 'formal'
        }
    ])

    templates.extend([
        {
            'category': 'volunteers-task-force',
            'name': 'volunteer-recruitment',
            'subject': 'Volunteer Opportunity: Help Make {event_name} Amazing!',
            'body': '''Dear {name},

We're recruiting volunteers to help make {event_name} an unforgettable experience!

VOLUNTEER ROLES AVAILABLE:
• Event setup and breakdown
• Participant registration
• Tech support and troubleshooting
• Food and beverage service
• Photography and documentation
• Social media management

EVENT DETAILS:
• Date: {date}
• Location: {location}
• Duration: {duration}
• Expected attendance: {participant_count}

WHAT WE PROVIDE:
• Volunteer t-shirt and materials
• Meals during the event
• Certificate of appreciation
• Networking opportunities
• Potential future opportunities

TIME COMMITMENT:
• {time_commitment}
• Flexible scheduling options
• Training provided

WHY VOLUNTEER:
• Give back to the tech community
• Learn event management skills
• Network with industry professionals
• Be part of something special

Ready to help? Sign up at {volunteer_link}

Questions? Contact {contact_email}

We can't do this without amazing volunteers like you!

Best,
{organization} Team
Volunteer Coordinator''',
            'tone': 'casual'
        },
        {
            'category': 'volunteers-task-force',
            'name': 'volunteer-training',
            'subject': 'Volunteer Training: {event_name} Preparation',
            'body': '''Hi {name},

Thank you for volunteering for {event_name}! Here's what you need to know:

TRAINING DETAILS:
• Date: {training_date}
• Time: {training_time}
• Location: {training_location}
• Duration: {training_duration}

WHAT TO EXPECT:
• Event overview and schedule
• Role-specific training
• Meet your fellow volunteers
• Q&A session
• Practice scenarios

YOUR ROLE: {volunteer_role}
RESPONSIBILITIES:
• {role_responsibilities}
• {role_expectations}

WHAT TO BRING:
• {training_materials}
• Enthusiasm and questions!

SCHEDULE OVERVIEW:
• {event_schedule}

We're excited to have you on our team!

Questions? Contact {contact_email}

See you at training!

Best,
{organization} Team
Volunteer Coordinator''',
            'tone': 'casual'
        },
        {
            'category': 'volunteers-task-force',
            'name': 'volunteer-day-of',
            'subject': 'Today is the Day! {event_name} Volunteer Briefing',
            'body': '''Hi {name},

{event_name} is today! Here's your volunteer briefing:

REPORTING TIME:
• Time: {report_time}
• Location: {report_location}
• What to wear: {volunteer_attire}

YOUR STATION: {volunteer_station}
SHIFT SCHEDULE:
• {shift_start} - {shift_end}
• Break times: {break_times}
• Meal times: {meal_times}

QUICK REMINDERS:
• Check in at volunteer desk
• Get your volunteer badge
• Review emergency procedures
• Have fun and be helpful!

EMERGENCY CONTACTS:
• Volunteer coordinator: {coordinator_contact}
• Medical emergency: {medical_contact}
• Tech support: {tech_contact}

We're counting on amazing volunteers like you to make this event special!

Thank you for your help!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'volunteers-task-force',
            'name': 'volunteer-thank-you',
            'subject': 'Thank You for Volunteering at {event_name}!',
            'body': '''Dear {name},

Thank you for being an amazing volunteer at {event_name}!

YOUR CONTRIBUTION:
• Role: {volunteer_role}
• Hours served: {hours_served}
• Tasks completed: {tasks_completed}
• Impact: {volunteer_impact}

EVENT SUCCESS METRICS:
• Participants served: {participants_served}
• Issues resolved: {issues_resolved}
• Positive feedback: {feedback_received}

We're continually impressed by volunteers like you who make our events possible.

Attached: Volunteer appreciation certificate

We'd love to have you back for future events!

Best regards,
{organization} Team
Volunteer Coordinator''',
            'tone': 'formal'
        }
    ])

    templates.extend([
        {
            'category': 'post-event-general',
            'name': 'survey-request',
            'subject': 'Help Us Improve: {event_name} Feedback Survey',
            'body': '''Hi {name},

Thank you for being part of {event_name}! Your feedback helps us improve future events.

FEEDBACK SURVEY:
• Takes only {survey_duration} minutes
• Covers all aspects of the event
• Helps us plan better experiences
• Your input directly impacts future events

SURVEY LINK: {survey_link}

WHAT WE'LL ASK ABOUT:
• Event organization and logistics
• Content quality and relevance
• Networking opportunities
• Overall experience and satisfaction

As a thank you, survey completers will be entered into a drawing for:
• {survey_incentive}

Your feedback is invaluable to us!

Complete the survey by {survey_deadline}.

Thank you!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'post-event-general',
            'name': 'content-share',
            'subject': 'Event Content: Photos, Videos & Resources from {event_name}',
            'body': '''Hi {name},

Thanks again for attending {event_name}! Here's all the content and resources from the event:

PHOTOS & VIDEOS:
• Event photos: {photos_link}
• Session recordings: {videos_link}
• Project showcases: {showcase_link}
• Behind-the-scenes: {bts_link}

RESOURCES & MATERIALS:
• Presentation slides: {slides_link}
• Workshop materials: {materials_link}
• Code repositories: {code_link}
• Additional resources: {resources_link}

PROJECTS & WINNERS:
• Winning projects: {winners_link}
• All participant projects: {projects_link}
• Judging feedback: {feedback_link}

STAY CONNECTED:
• Community forum: {community_link}
• Newsletter: {newsletter_link}
• Social media: {social_links}

We hope you enjoyed the event and will join us for future ones!

Best,
{organization} Team''',
            'tone': 'casual'
        },
        {
            'category': 'post-event-general',
            'name': 'future-events',
            'subject': 'Upcoming Events from {organization}',
            'body': '''Dear {name},

Hope you're still enjoying the post-{event_name} momentum! We have exciting upcoming events you might be interested in:

UPCOMING EVENTS:
• {next_event}: {next_date} - {next_description}
• {monthly_meetup}: {meetup_date} - {meetup_description}
• {workshop_series}: {workshop_date} - {workshop_description}
• {annual_conference}: {conference_date} - {conference_description}

WHY ATTEND AGAIN:
• Connect with familiar faces
• Build on what you learned
• Discover new technologies
• Expand your network
• Win more prizes!

SPECIAL ALUMNI BENEFITS:
• Early registration access
• Alumni networking events
• Priority mentorship matching
• Exclusive workshops
• Community leadership opportunities

Stay connected:
• Website: {website}
• Newsletter: {newsletter}
• Community: {community_link}
• Social: {social_links}

We can't wait to see you at future events!

Best,
{organization} Team''',
            'tone': 'casual'
        }
    ])

    return templates