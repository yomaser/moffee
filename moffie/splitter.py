from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from copy import deepcopy
import yaml
import re
from mdbeamer.utils.md_helper import get_header_level, is_divider, is_empty, contains_image, contains_deco

@dataclass
class PageOption:
    default_h1: bool = False
    default_h2: bool = True
    default_h3: bool = True
    layout: str = "top-down"

@dataclass
class Chunk:
    content: str
    type: str = "paragraph"


@dataclass
class Page:
    raw_md: str
    option: PageOption
    chunks: List[Chunk] = field(default_factory=list)
    h1: Optional[str] = None
    h2: Optional[str] = None
    h3: Optional[str] = None
    deco: Dict[str, Any] = field(default_factory=dict)

    @property
    def title(self) -> Optional[str]:
        return self.h1 or self.h2 or self.h3

    @property
    def subtitle(self) -> Optional[str]:
        if self.h1:
            return self.h2 or self.h3
        elif self.h2:
            return self.h3
        return None
    
    def chunk(self):
        """
        Split raw_md into chunks based on the following criteria:
        - Before/after lines that contain images
        - Two consecutive blank lines

        Modifies the page's 'chunks' list in-place.
        """
        self._preprocess()
        
        lines = self.raw_md.split("\n")
        current_chunk = []
        blank_line_count = 0

        for i, line in enumerate(lines):
            if contains_image(line):
                if current_chunk:
                    self.chunks.append(Chunk(content="\n".join(current_chunk)))
                    current_chunk = []
                self.chunks.append(Chunk(content=line, type="image"))
                blank_line_count = 0
            elif is_empty(line):
                blank_line_count += 1
                if blank_line_count == 2:
                    if current_chunk:
                        self.chunks.append(Chunk(content="\n".join(current_chunk)))
                        current_chunk = []
                    blank_line_count = 0
                else:
                    current_chunk.append(line)
            else:
                current_chunk.append(line)
                blank_line_count = 0

            # Check if it's the last line
            if i == len(lines) - 1 and current_chunk:
                self.chunks.append(Chunk(content="\n".join(current_chunk)))

    def _preprocess(self):
        """
        Additional processing needed for the page.
        Modifies raw_md in place.
        
        - Removes headings 1-3
        - Stripes
        """
        
        lines = self.raw_md.splitlines()
        lines = [l for l in lines if not (1 <= get_header_level(l) <= 3)]
        self.raw_md = "\n".join(lines).strip()


def parse_frontmatter(document: str) -> Tuple[str, PageOption]:
    """
    Parse the YAML front matter in a given markdown document.

    :param document: Input markdown document as a string.
    :return: A tuple containing the document with front matter removed and the PageOption.
    """
    document = document.strip()
    front_matter = ""
    content = document

    # Check if the document starts with '---'
    if document.startswith('---'):
        parts = document.split('---', 2)
        if len(parts) >= 3:
            front_matter = parts[1].strip()
            content = parts[2].strip()

    # Parse YAML front matter
    try:
        yaml_data = yaml.safe_load(front_matter) if front_matter else {}
    except yaml.YAMLError:
        yaml_data = {}

    # Create PageOption from YAML data
    option = PageOption(
        default_h1=yaml_data.get('default_h1', False),
        default_h2=yaml_data.get('default_h2', True),
        default_h3=yaml_data.get('default_h3', True),
        layout=yaml_data.get('layout', 'top-down')
    )

    return content, option


def parse_deco(
    line: str, base_option: Optional[PageOption] = None
) -> Tuple[Optional[Dict[str, str]], Optional[PageOption]]:
    """
    Parses a deco (custom decorator) line and returns a dictionary of key-value pairs.
    If base_option is provided, it updates the option with matching keys from the deco.

    :param line: The line containing the deco
    :param base_option: Optional PageOption to update with deco values
    :return: A tuple containing:
             - A dictionary of remaining key-value pairs if the line is a valid deco, None otherwise
             - An updated PageOption if base_option was provided, None otherwise
    """
    deco_match = re.match(r"^\s*@\((.*?)\)\s*$", line)
    if not deco_match:
        raise ValueError(f"Input line should contain a deco, {line} received.")

    deco_content = deco_match.group(1)
    pairs = re.findall(r"(\w+)\s*=\s*([^,]+)(?:,|$)", deco_content)
    deco = {key.strip(): value.strip() for key, value in pairs}

    if base_option is None:
        return deco, None

    updated_option = deepcopy(base_option)
    remained_deco = {}

    for key, value in deco.items():
        if hasattr(updated_option, key):
            setattr(updated_option, key, parse_value(value))
        else:
            remained_deco[key] = parse_value(value)

    return remained_deco, updated_option


def parse_value(value: str):
    """Helper function to parse string values into appropriate types"""
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.isdigit():
        return int(value)
    elif value.replace(".", "", 1).isdigit():
        return float(value)
    return value


def paginate(document: str, option: PageOption = None) -> List[Page]:
    """
    Paginates a markdown document into slide pages.

    Splitting criteria:
    - New h1/h2/h3 header (except when following another header)
    - More than 8 non-empty lines in a page
    - Divider (___, ***, +++)

    :param document: Input markdown document as a string.
    :param option: PageOption object containing pagination configuration. Will try to parse from document yaml area if None.
    :return: List of Page objects representing paginated slides.
    """
    pages: List[Page] = []
    current_page_lines = []
    current_h1 = current_h2 = current_h3 = None
    line_count = 0
    prev_header_level = 0

    document, parsed_option = parse_frontmatter(document)
    if option == None:
        option = parsed_option

    lines = document.split("\n")

    def create_page():
        nonlocal current_page_lines, line_count, current_h1, current_h2, current_h3, option
        # Only make new page if has non empty lines

        if all([l.strip() == '' for l in current_page_lines]):
            return

        deco = {}
        raw_md = ""
        local_option = deepcopy(option)
        for line in current_page_lines:
            if contains_deco(line):
                _deco, local_option = parse_deco(line, local_option)
                deco = {**deco, **_deco}
            else:
                raw_md += "\n" + line

        page = Page(raw_md=raw_md, 
                    option=local_option, 
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    deco=deco)

        pages.append(page)
        current_page_lines = []
        line_count = 0
        current_h1 = current_h2 = current_h3 = None

    for _, line in enumerate(lines):
        header_level = get_header_level(line)

        # Check if this is a new header and not consecutive
        # Only break at heading 1-3
        is_downstep_header_level = prev_header_level == 0 or prev_header_level > header_level
        is_more_than_level_4 = prev_header_level > header_level >= 3
        if header_level > 0 and is_downstep_header_level and not is_more_than_level_4:
            # Check if the next line is also a header
            create_page()

        # if line_count > 8:
            # create_page()

        if is_divider(line):
            create_page()
            continue

        match header_level:
            case 1:
                current_h1 = line.lstrip("#").strip()
            case 2:
                current_h2 = line.lstrip("#").strip()
            case 3:
                current_h3 = line.lstrip("#").strip()
            case _:
                pass  # Handle other cases or do nothing

        current_page_lines.append(line)
        if not is_empty(line):
            line_count += 1

        if header_level > 0:
            prev_header_level = header_level
        if header_level == 0 and not is_empty(line) and not contains_deco(line):
            prev_header_level = 0

    # Create the last page if there's remaining content
    create_page()

    # Process each page
    env_h1 = env_h2 = env_h3 = None
    for page in pages:
        inherit_h1 = page.option.default_h1
        inherit_h2 = page.option.default_h2
        inherit_h3 = page.option.default_h3
        if page.h1 != None:
            env_h1 = page.h1
            env_h2 = env_h3 = None
            inherit_h1 = inherit_h2 = inherit_h3 = False
        if page.h2 != None:
            env_h2 = page.h2
            env_h3 = None
            inherit_h2 = inherit_h3 = False
        if page.h3 != None:
            env_h3 = page.h3
            inherit_h3 = False
        if inherit_h1:
            page.h1 = env_h1
        if inherit_h2:
            page.h2 = env_h2
        if inherit_h3:
            page.h3 = env_h3

        page.chunk()

    return pages