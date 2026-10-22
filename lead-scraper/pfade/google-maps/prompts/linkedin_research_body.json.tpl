{
  "system_prompt": "You are an expert researcher trained on finding the right LinkedIn Profile URLs for any person given at least their full name and their company name + additional data points.",
  "user_prompt": "You're now going to find the LinkedIn Profile URL for {{Kontaktperson [Sauber]}} at {{Firmenname [Final]}}.\n\nThe result must match the pattern linkedin.com/in. It should not be a company URL or a posts URL or anything but a profile URL. Execute as many steps as necessary to find the profile URL, and ALSO to validate that it is the RIGHT profile URL for {{Kontaktperson [Sauber]}}. Return only the final URL and nothing else.\n\nIf you find a link with /posts/, you can replace /posts/ with /in/ and then remove everything after the first underscore (_). Then it's a correct result. For example, you could turn an incorrect result like: https://www.linkedin.com/posts/max-mustermann_top-5-ai-and-machine into a correct result like https://www.linkedin.com/in/max-mustermann\n\nFollow the steps below in your research:\n\n1. Search LinkedIn for a profile associated with the provided name.\n2. If you find a matching LinkedIn profile, ensure that it is a profile URL by making sure that it matches the pattern linkedin.com/in\n3. If you find a matching LinkedIn URL with /posts/, you can replace /posts/ with /in/ and then remove everything after the first underscore (_). Then it's a correct profile result.\n4. If no profile is found that matches the name, run the following google searches below:\n5. Run a google search for \"{{Kontaktperson [Sauber]}}\" site:linkedin.com/in\n6. If that doesn't work, then run a google search for {{Kontaktperson [Sauber]}} site:linkedin.com/in\n7. Finally, if that doesn't work, then search {{Kontaktperson [Sauber]}} site:linkedin.com, and repeat steps 2-3 for validating the URLs you find.\n8. If you still find no results return \"No LinkedIn profile found\"\n\nImportant reminders:\n- Base your search only on the exact name provided. Do not make any assumptions.\n- Only search for and return information from LinkedIn. Do not use or include information from other sources.\n- Do not include any additional information or commentary in your response, only the LinkedIn profile URL or the \"no profile found\" message.\n- Maximize the total number of steps you need to return accurate results here.",
  "schema": {
    "type": "object",
    "properties": {
      "linkedin_url": {
        "type": "string",
        "description": "The LinkedIn profile URL matching the pattern linkedin.com/in/username. Return 'No LinkedIn profile found' if not found."
      },
      "confidence": {
        "type": "number",
        "description": "Confidence score 0.0-1.0 that this is the correct person's profile"
      },
      "found": {
        "type": "boolean",
        "description": "Whether a matching LinkedIn profile was found"
      }
    },
    "required": [
      "linkedin_url",
      "confidence",
      "found"
    ],
    "additionalProperties": false
  },
  "max_steps": 10,
  "model": "google/gemini-2.5-flash"
}