version: "1.0"
workspace: "Simon_Aguilera_Automations"
timezone: "America/Santiago"

integrations:
  gmail:
    enabled: true
    permissions: [read, send]
  gcal:
    enabled: true
    calendars: [primary, work, personal, clients]
  notion:
    enabled: true
    databases:
      - "Notion_Project_DB"
      - "Notion_Journal_DB"
  github:
    enabled: true
    repos:
      - "nomad3/dentalerp"
      - "nomad3/agentprovision"
      - "nomad3/mcp-server"

automations:

  # 1. Silvercreek Payment Follow-Up
  - id: silvercreek_followup
    trigger:
      type: schedule
      cron: "0 9 * * FRI"  # every Friday 09:00 Santiago
    actions:
      - type: gmail.send
        to: "barbara.marra@silvercreekdp.com"
        subject: "Silvercreek | Contract & Initial Payment Follow-Up"
        body: |
          Hi Barbara,
          I hope you’re well.
          Just checking in to confirm receipt of the initial invoice and signed contract.
          Please let me know once the payment is processed so we can kick off the next sprint.
          Best,
          Simon

  # 2. Daily Deep Work Protection
  - id: daily_deep_work
    trigger:
      type: schedule
      cron: "0 8 * * MON-FRI"
    actions:
      - type: gcal.block_time
        title: "Deep Work Block #1"
        start: "08:00"
        end: "09:15"
        color: "orange"
        description: "Protected focus time — MCP / DentalERP / Silvercreek"
        set_busy: true

  # 3. MCP & DentalERP Progress Summary
  - id: project_summary
    trigger:
      type: schedule
      cron: "0 17 * * FRI"
    actions:
      - type: github.summary
        repos:
          - "nomad3/dentalerp"
          - "nomad3/mcp-server"
        since: "last_friday"
      - type: gmail.send
        to: "saguilera1608@gmail.com"
        subject: "Weekly Engineering Summary — DentalERP & MCP"
        body_from: github.summary
        attach_logs: true

  # 4. Weekly Team Planning Sync Creation
  - id: planning_syncs
    trigger:
      type: schedule
      cron: "0 10 * * MON"
    actions:
      - type: gcal.create_event
        title: "Weekly Planning Sync (All Projects)"
        start: "10:30"
        end: "11:15"
        attendees:
          - "sergio@agentprovision.com"
          - "james@agentprovision.com"
          - "erick@agentprovision.com"
        description: |
          Review priorities:
          - Silvercreek contract status
          - EventBridge roadmap
          - Banco Falabella dashboards
          - DentalERP & MCP technical progress
        color: "purple"
        recurrence: "WEEKLY"

  # 5. Contract / Invoice Tracker
  - id: contract_tracker
    trigger:
      type: notion.database_update
      database: "Notion_Project_DB"
      filter:
        property: "Status"
        equals: "Contract Ready"
    actions:
      - type: gmail.send
        to_property: "Client Email"
        subject: "Contract & Invoice Ready for Review"
        body_template: |
          Hi {{ClientName}},
          The contract for {{ProjectName}} is now ready for your review.
          Once signed, the invoice will be sent automatically.
          Regards,
          Simon

  # 6. Journal Reminder & Reflection Log
  - id: daily_journal
    trigger:
      type: schedule
      cron: "0 7 * * *"
    actions:
      - type: chat.reminder
        message: |
          🌅 Morning Journal Time!
          1️⃣ Wins from yesterday
          2️⃣ Lessons learned
          3️⃣ Energy level (1–10)
          4️⃣ Gratitude (3 things)
          5️⃣ Priority for today
      - type: notion.new_entry
        database: "Notion_Journal_DB"
        fields:
          Date: "{{today}}"
          Status: "Open"
          Prompt: "Morning Reflection"

  # 7. Assistant Hiring Follow-Up
  - id: assistant_hiring
    trigger:
      type: schedule
      cron: "0 16 * * THU"
    actions:
      - type: gmail.send
        to: "yani@agentprovision.com"
        subject: "Assistant Role Progress"
        body: |
          Hi Yani,
          Just checking in about this week’s progress.
          Could you please update your task status and share any blockers?
          Thanks,
          Simon

  # 8. Weekly Journal + Performance Summary
  - id: weekly_journal_summary
    trigger:
      type: schedule
      cron: "0 18 * * SUN"
    actions:
      - type: notion.aggregate
        database: "Notion_Journal_DB"
        timeframe: "last_week"
      - type: chat.message
        message_from: notion.aggregate
        prefix: "🧭 Weekly Reflection Summary"
