# Copilot Instructions: Tommy Garner's Academic Portfolio

This is an academic portfolio website built with Jekyll using the Academic Pages template. The site showcases data science and analytics projects focused on the live entertainment and ticketing industry.

## Local Development

### Running the Site
- **Quick start**: `bundle exec jekyll serve -l -H localhost` (serves at localhost:4000)
- **With auto-rebuild**: Jekyll automatically rebuilds on Markdown/HTML changes
- **Configuration changes**: Require stopping and restarting Jekyll

### Build Commands
- **Install dependencies**: `bundle install` (install Ruby gems)
- **JavaScript build**: `npm run build:js` (uglifies and concatenates JS assets)
- **Watch JS changes**: `npm run watch:js` (auto-rebuilds JS on file changes)

### Docker Alternative
```bash
chmod -R 777 .
docker compose up
```
Access at localhost:4000

## Site Architecture

### Jekyll Collections
The site uses five main content collections defined in `_config.yml`:
- `_posts/`: Blog posts with date-based URLs
- `_portfolio/`: Project showcases 
- `_publications/`: Academic publications
- `_talks/`: Conference presentations
- `_teaching/`: Course materials

### Content Patterns

#### Blog Posts (`_posts/`)
- **Naming**: `YYYY-MM-DD-title.md` format
- **Front matter**: Includes `layout: single`, `title`, `date`, `tags`, `excerpt`
- **Features**: Support for TOC (`toc: true`), wide layout (`classes: wide`)
- **Interactive content**: Often embed Streamlit dashboards via iframes

#### Portfolio Items (`_portfolio/`)
- **Project-focused**: Showcase completed data science projects
- **Rich media**: Include charts, images, and interactive visualizations
- **Business impact**: Emphasize real-world applications and results

#### Content Generation
The `markdown_generator/` folder contains Jupyter notebooks and Python scripts to auto-generate content from TSV files:
- `publications.tsv` → individual publication markdown files
- `talks.tsv` → individual talk markdown files

## Key Conventions

### Content Writing
- **Domain focus**: Live entertainment, ticketing, venue operations, and fan experience
- **Technical depth**: Balance accessibility with technical rigor
- **Business context**: Always include practical impact and business value
- **Interactive elements**: Prefer embedded dashboards and visualizations over static images

### File Organization
- **Images**: Store project images in `_portfolio/` alongside markdown files
- **Assets**: Global assets go in `assets/`, `images/`, or `files/`
- **Generated content**: Use markdown generator scripts for bulk content creation

### Styling
- **Custom CSS**: Include inline `<style>` blocks for component-specific styling
- **Responsive design**: Use `classes: wide` for content that benefits from full width
- **Interactive embeds**: Consistent styling for Streamlit and external dashboard embeds

## Technical Stack

### Frontend
- **Theme**: Academic Pages (fork of Minimal Mistakes)
- **CSS**: Sass preprocessing with custom overrides
- **JavaScript**: jQuery + custom plugins (compiled via npm scripts)
- **Math**: MathJax for equations
- **Diagrams**: Jekyll-mermaid plugin support

### Data & Analytics
- **Streamlit**: External dashboards embedded via iframes
- **Charts**: Plotly.js for interactive visualizations
- **Data sources**: Often references seatdata.io and live entertainment data

### Deployment
- **Hosting**: GitHub Pages
- **Domain**: tommygarner.github.io
- **CI/CD**: Automatic builds on push to main branch

## Development Workflow

### Content Creation
1. **New blog post**: Create `_posts/YYYY-MM-DD-title.md` with appropriate front matter
2. **New project**: Create `_portfolio/project-name.md` with project assets
3. **Bulk content**: Use markdown generator scripts for publications/talks

### Theme Customization
1. **Layout changes**: Modify files in `_layouts/` and `_includes/`
2. **Styling**: Update `_sass/` files or add custom CSS
3. **JavaScript**: Edit source files, then run `npm run build:js`

### Testing
- Always test locally before deploying
- Check responsive design at different screen sizes
- Verify embedded content loads correctly
- Test navigation and internal links

## AI Collaboration Notes

Based on the existing GEMINI.md file, follow these principles:
- **Transparency**: Provide clear reasoning for suggested changes
- **Surgical precision**: Make minimal, targeted updates to maintain site integrity
- **Critical questioning**: Ask clarifying questions about content strategy and technical choices
- **Metacognitive approach**: Use deliberate reflection before major decisions