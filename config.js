/* OPERATOR RECON — funnel config. Single source of truth for every
   outbound link the app and the /start/ landing page use.
   Fill these in, commit, push. Blank value = that button stays hidden. */
window.RECON_CONFIG = {
  // Kit (ConvertKit) form ID — the number in the form's embed URL:
  // app.kit.com/forms/<ID>/... . Blank = email capture hidden.
  KIT_FORM_ID: "",

  // Field Guide checkout. Primary button = Lemon Squeezy, secondary = Shopify.
  FIELD_GUIDE_LEMON_URL: "",
  FIELD_GUIDE_SHOPIFY_URL: "",
  FIELD_GUIDE_PRICE: "",          // e.g. "$19" — shown on the button. Blank = no price shown.

  // Substack — free field notes, secondary channel.
  SUBSTACK_URL: "https://chrisstewarta2a.substack.com"
};
