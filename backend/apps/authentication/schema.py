"""
OpenAPI schema extensions for drf-spectacular.
Registers SupabaseJWTAuthentication for API documentation.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class SupabaseJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Extension pour documenter SupabaseJWTAuthentication dans OpenAPI/Swagger.
    """

    target_class = "apps.authentication.backends.SupabaseJWTAuthentication"
    name = "SupabaseJWTAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token from Supabase authentication. "
            "Include the token in the Authorization header as: Bearer <token>",
        }