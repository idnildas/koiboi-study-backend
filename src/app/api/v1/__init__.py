# Routers and endpoint handlers — import directly from their submodules.
#
# Routers:
#   from app.api.v1.health    import router as health_router
#   from app.api.v1.auth      import router as auth_router
#   from app.api.v1.users     import router as users_router
#   from app.api.v1.subjects  import router as subjects_router
#   from app.api.v1.topics    import router as topics_router
#   from app.api.v1.notes     import router as notes_router
#   from app.api.v1.materials import router as materials_router
#   from app.api.v1.snippets  import router as snippets_router
#   from app.api.v1.master_data import router as master_router
#
# Endpoints:
#   from app.api.v1.health      import health_check, readiness_check, liveness_check
#   from app.api.v1.master_data import list_avatar_styles, get_avatar_style, list_avatar_colors, list_tint_palette
#   from app.api.v1.auth        import sign_up, sign_in, sign_out, forgot_password, reset_password, change_password
#   from app.api.v1.users       import get_profile, update_profile
#   from app.api.v1.subjects    import list_subjects, create_subject, update_subject, delete_subject
#   from app.api.v1.topics      import list_topics, create_topic, update_topic, delete_topic
#   from app.api.v1.notes       import list_notes, create_note, get_note, update_note, delete_note
#   from app.api.v1.materials   import list_materials, upload_material, update_material, download_material, delete_material
#   from app.api.v1.snippets    import list_snippets, create_snippet, update_snippet, delete_snippet
