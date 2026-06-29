# Insight Academia — insightacademia.org

Static website for Insight Academia. Built with plain HTML/CSS/JS — no build step, no dependencies.

---

## File structure

```
insightacademia/
├── index.html          Home page
├── services.html       Services page
├── about.html          About page
├── contact.html        Contact page
├── css/style.css       All styles
├── js/main.js          Navigation, FAQ accordion, contact form
├── CNAME               Custom domain for GitHub Pages
└── .nojekyll           Disables Jekyll on GitHub Pages
```

---

## Step 1: Configure your details

Open `js/main.js` and update the CONFIG object at the top:

```js
const CONFIG = {
  whatsapp: 'YOURNUMBER',         // e.g. '919876543210' (no + or spaces)
  whatsappMessage: '...',         // Pre-filled message — edit if needed
  formspree: 'https://formspree.io/f/YOURFORMID',   // See Step 2
  email: 'hello@insightacademia.org',
};
```

---

## Step 2: Set up Formspree (contact form)

1. Go to https://formspree.io and create a free account
2. Click "New Form" — name it "Insight Academia Contact"
3. Copy the form endpoint URL (looks like `https://formspree.io/f/xyzabc12`)
4. Paste it into `CONFIG.formspree` in `js/main.js`

Free tier: 50 submissions/month. Upgrade if needed.

---

## Step 3: Deploy to GitHub Pages

1. Create a GitHub account at https://github.com if you don't have one
2. Create a new repository — name it anything (e.g. `insightacademia-site`)
3. Upload all files from this folder into the repository (drag and drop, or use git)
4. Go to **Settings → Pages**
5. Under "Source", select **Deploy from a branch**
6. Set Branch to **main**, folder to **/ (root)** → click Save
7. GitHub will give you a URL like `https://username.github.io/insightacademia-site`

Your site is now live at that URL. Test it before pointing your domain.

---

## Step 4: Connect your custom domain (insightacademia.org)

In GitHub → Settings → Pages → Custom domain, enter `insightacademia.org` and save.

Then go to your domain registrar (wherever you bought insightacademia.org) and add these DNS records:

**A records** (for the apex domain `insightacademia.org`):

| Type | Name | Value          |
|------|------|----------------|
| A    | @    | 185.199.108.153 |
| A    | @    | 185.199.109.153 |
| A    | @    | 185.199.110.153 |
| A    | @    | 185.199.111.153 |

**CNAME record** (for `www`):

| Type  | Name | Value                         |
|-------|------|-------------------------------|
| CNAME | www  | yourusername.github.io        |

DNS propagation takes 15 minutes to 48 hours. Once live, GitHub Pages will also issue a free SSL certificate — enable "Enforce HTTPS" in Pages settings once it appears.

---

## Optional: Replace the About page photo

In `about.html`, find the `<div class="about-image-placeholder">` element and replace it with:

```html
<img src="images/your-photo.jpg" alt="Insight Academia" style="width:100%;border-radius:var(--radius-xl);object-fit:cover;aspect-ratio:4/5;">
```

Create an `images/` folder in the root and add your photo there.

---

## Updating content

All copy is in the HTML files. Search for any text you want to change and edit directly.
The copyright year in the footer is in each HTML file — update it annually.
