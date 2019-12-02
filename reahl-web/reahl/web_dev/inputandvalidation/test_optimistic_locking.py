

# A form cannot be submitted if the values it was originally rendered with have changed in the backend by other means before the form gets submitted.
# When presented with such an error, the user can click on a button to reset all inputs to the now-current values (if using the not-yet-there "ResetForm" in non-bootstrap stuff)
#   - this also clears all possible form (the current form) exceptions and remembered input values

# Scenario: user B changes something AFTER user A has gotten a DomainException but before user B submits correct data again.

# (move to a bootstrap-specific test:) if using FormLayout.add_alert_for_domain_exception

# Only VISIBLE PrimitiveInput value data is taken into account by default for such optimistic locking, but:
#  if an input becomes readonly (or not readonly) since last rendered, it is also considered as having changed.
#  passing ignore_concurrency=True prevents a PrimitiveInput from taking part, despite being visible, and despite its readablity
#  any VISIBLE Widget can take part, if it overrides its concurrency_hash_strings method, and append a string representing its value to the yielded values


# If the user submits to a form that is no longer present on the current view (because of changes data as well), 
# the user is sent to the general error page and all form input/exceptions for all forms on the view are cleared.
# When clicking on the OK button on said error page, the user is taken back to the view, but sees it refreshed to new values.
