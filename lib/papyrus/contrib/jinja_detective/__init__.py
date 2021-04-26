"""
Hacks for debugging/introspecting Jinja2 templates.

**Features**

Adds a "jinja debug toolbar", inspired by ``django_debug_toolbar``, to all rendered HTML templates.
The panel displays the following debugging information:

- All templates, whether static or dynamic, referenced (with ``include`` ``extends`` ``import``) by the rendered template, recursively.
  - Also output the origin of all references.
- Context available to each template.
- Full paths to each template.

**Limitations**

The debug toolbar HTML currently relies on TailwindCSS and AlpineJS.

**Configuration**

``jinja_detective_enabled``
    Whether to enable the debug toolbar.

``jinja_detective_insert_before``
    The HTML for the debug toolbar will be inserted before this string.
"""
from __future__ import annotations

import dataclasses
import itertools
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import jinja2.environment
import jinja2.loaders
import sphinx.application
import sphinx.builders
import sphinx.config
import sphinx.jinja2glue

PACKAGE_DIR = Path(__file__).parent
RENDERED_CONTEXT_ATTR = "rendered_ctx"
JINJA_DETECTIVE_ENABLED = "jinja_detective_enabled"
JINJA_DETECTIVE_INSERT_BEFORE = "jinja_detective_insert_before"
JINJA_DETECTIVE_TEMPLATE_NAME = "jinja_detective.html"

logger = logging.getLogger(__name__)


def setup(app: sphinx.application.Sphinx) -> None:
    app.add_config_value(JINJA_DETECTIVE_ENABLED, default=False, rebuild="html", types=[bool])
    app.add_config_value(JINJA_DETECTIVE_INSERT_BEFORE, default="</body>", rebuild="html", types=[str])
    app.connect("config-inited", cb_config_inited)
    # XXX temporary
    app.add_css_file("https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css")
    app.add_js_file("https://cdn.jsdelivr.net/gh/alpinejs/alpine@v2.x.x/dist/alpine.min.js")


def cb_config_inited(app: sphinx.application.Sphinx, config: sphinx.config.Config) -> None:
    if config[JINJA_DETECTIVE_ENABLED]:
        config["template_bridge"] = _get_class_import_string(DebugTemplateLoader)
        config["templates_path"].append(str(PACKAGE_DIR / "templates"))  # type: ignore


@dataclasses.dataclass
class TemplateOrigin:
    path: Path
    name: str
    lineno: int  # 1-based
    line: str


class DebugTemplateLoader(sphinx.jinja2glue.BuiltinTemplateLoader):
    #: list of ``(template, parent)``
    #: - ``parent`` is the origin of the ``template``, or ``None`` if ``template`` is the root template.`
    #: - ``template`` is the loaded template.
    #:   Additionally, the context with which ``template`` was rendered is stored on the ``RENDERED_CONTEXT_ATTR`` attribute.
    load_history: List[Tuple[jinja2.environment.Template, Optional[TemplateOrigin]]]
    insert_before: str

    def init(self, builder: sphinx.builders.Builder, *args: Any, **kwargs: Any) -> None:
        self.insert_before = builder.config[JINJA_DETECTIVE_INSERT_BEFORE]
        return super().init(builder, *args, **kwargs)

    def render(self, template: str, context: Any) -> str:  # type: ignore
        if template != JINJA_DETECTIVE_TEMPLATE_NAME:
            self.load_history = []
        ret = super().render(template, context)
        if template == JINJA_DETECTIVE_TEMPLATE_NAME:
            return ret
        insert_idx = ret.find(self.insert_before)
        if insert_idx == -1:
            logger.warning(
                f"{JINJA_DETECTIVE_INSERT_BEFORE} ('{self.insert_before}') not found in template '{template}'."
            )
        else:
            self.environment.filters["resolvepath"] = lambda v: Path(v).resolve()
            debug_toolbar_html = self.render(
                JINJA_DETECTIVE_TEMPLATE_NAME, {"load_history": self.load_history}
            )
            ret = ret[:insert_idx] + debug_toolbar_html + ret[insert_idx:]
        return ret

    def load(
        self,
        environment: jinja2.environment.Environment,
        name: str,
        globals: Any = None,  # pylint: disable=redefined-builtin
    ) -> jinja2.environment.Template:
        template: jinja2.environment.Template = super().load(environment, name, globals=globals)

        root_render_func_og = template.root_render_func  # type: ignore
        setattr(template, RENDERED_CONTEXT_ATTR, None)

        def root_render_func_patched(ctx: Any) -> Any:
            setattr(template, RENDERED_CONTEXT_ATTR, ctx)
            return root_render_func_og(ctx)

        template.root_render_func = root_render_func_patched  # type: ignore

        parent = None
        if self.load_history:
            parent = find_parent_template()
        self.load_history.append((template, parent))
        return template


def get_line_from_file(path: Path, lineno: int) -> str:
    with open(path) as f:
        for i, line in enumerate(f, start=1):
            if i == lineno:
                return line
    return "<unknown>"


def find_parent_template() -> Optional[TemplateOrigin]:
    # Caution: dirty frame hacks ahead!

    # Use walk_stack instead of extract_stack in order to have access to f_globals
    for frame, _lineno in itertools.islice(traceback.walk_stack(None), 10):
        co = frame.f_code
        path = Path(co.co_filename).resolve()
        try:
            template: jinja2.environment.Template = frame.f_globals["__jinja_template__"]
        except KeyError:
            continue
        template_lineno: int = template.get_corresponding_lineno(frame.f_lineno)  # type: ignore
        line = get_line_from_file(path, template_lineno).strip()
        return TemplateOrigin(path=path, name=template.name or "NO NAME", lineno=template_lineno, line=line)
    return None


def _get_class_import_string(cls: Type[Any]) -> str:
    return ".".join((cls.__module__, cls.__name__))
