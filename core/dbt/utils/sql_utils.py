import re 
from typing import Optional

def normalize_compiled_sql(sql:Optional[str]) -> Optional [str] :
    if sql is None:
        return None

    normalized = sql.strip()

    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized
