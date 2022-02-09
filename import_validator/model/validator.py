# generated by datamodel-codegen:
#   filename:  ignore.json
#   timestamp: 2022-02-09T03:43:36+00:00

# TODO add validator for validate workspace with root workspace

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, conlist


class Description(BaseModel):
    time_updated: Optional[int]
    time_created: int
    user_id: str
    entry_id: str
    text: str
    workspace: str


class Activity(BaseModel):
    time_created: int
    user_id: str
    entry_title: str
    workspace: str
    entry_id: str
    commit_id: Optional[str]
    activity_id: str
    message: str
    type: str


class Comment(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    comment_id: str
    entry_id: str
    commit_id: str
    text: str
    workspace: str


class Like(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    like_id: str
    commit_id: str
    entry_id: str
    workspace: str


class CommitTag(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    tag_id: str
    commit_id: str
    entry_id: str
    text: str
    workspace: str


class Commit(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    workspace: str
    commit_id: str
    entry_id: str
    type: str
    data: str
    title: str
    marked: bool
    locked: Any
    comments: conlist(Comment, min_items=0)
    likes: conlist(Like, min_items=0)
    tags: conlist(CommitTag, min_items=0)


class Flag(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    flag_id: str
    entry_id: str
    flag: str
    workspace: str


class Note(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    note_id: str
    entry_id: str
    commit_id: str
    workspace: str
    text: str


class Entry(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    entry_id: str
    category: str
    priority: str
    title: str
    workspace: str
    description: Optional[Description]
    activities: List[Activity]
    commits: List[Commit]
    flags: conlist(Flag, min_items=0)
    notes: Optional[List[Note]]
    entry_tags: Optional[List[str]]


class Workspace(BaseModel):
    time_updated: int
    time_created: int
    user_id: str
    workspace: str
    description: Optional[str]
    entries: List[Entry]
    export_time: int
    private: Any
    locked: Any
    login: str
    password: str
    url: str
