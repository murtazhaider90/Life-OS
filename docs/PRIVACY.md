# PRIVACY

Life OS is local-first. Plans, study evidence, activity/context data and uploaded course material stay in the local SQLite database unless you explicitly configure an external integration.

## Academic Brain

PDF/TXT/Markdown/DOCX/PPTX extraction and FTS retrieval run locally.

By default there is no configured academic AI provider. In local extractive mode, course text is not sent to a cloud model.

If you configure `LIFE_OS_AI_BASE_URL` and a model, the selected retrieved source chunks and your academic question can be sent to that endpoint for synthesis. This is an explicit configuration boundary. The API key remains an environment secret rather than a database field.

Deleting a course document deletes its structured document/chunk records and linked extracted academic records, and removes its chunks from the local FTS index.

## Voice assistant

Raw side-assistant conversations are not persisted. Accepted commands create only structured records needed by the feature.

Windows/browser speech processing is a separate privacy boundary and may use an online speech-recognition service depending on the user's OS/browser settings. Life OS itself does not continuously record microphone audio.

## Activity/context

Activity collection deliberately excludes keystrokes, clipboard data, screenshots, page contents and full URL paths/query strings. Browser activity stores hostname only.

Sleep, training and meal data is opt-in. Missing context is not silently interpreted as normality.

## External integrations

AdGuard and optional AI-provider credentials are environment-only. No current component performs continuous webcam capture, continuous microphone recording, private-message ingestion, password collection or silent network blocking.
