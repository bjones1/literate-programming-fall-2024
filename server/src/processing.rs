/// Copyright (C) 2023 Bryan A. Jones.
///
/// This file is part of the CodeChat Editor. The CodeChat Editor is free
/// software: you can redistribute it and/or modify it under the terms of the
/// GNU General Public License as published by the Free Software Foundation,
/// either version 3 of the License, or (at your option) any later version.
///
/// The CodeChat Editor is distributed in the hope that it will be useful, but
/// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
/// or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
/// more details.
///
/// You should have received a copy of the GNU General Public License along with
/// the CodeChat Editor. If not, see
/// [http://www.gnu.org/licenses](http://www.gnu.org/licenses).
///
/// # `processing.rs` -- Transform source code to its web-editable equivalent and back
// ## Imports
//
// ### Standard library
//
// For commented-out caching code.
/**
use std::collections::{HashMap, HashSet};
use std::fs::Metadata;
use std::io;
use std::ops::Deref;
use std::rc::{Rc, Weak};
*/
use std::ffi::OsStr;
use std::path::Path;
use std::path::PathBuf;

// ### Third-party
use lazy_static::lazy_static;
use pulldown_cmark::{html, Options, Parser};
use regex::Regex;

// ### Local
use crate::lexer::{
    source_lexer, CodeDocBlock, DocBlock, LanguageLexerCompiled, LanguageLexersCompiled,
};
use crate::webserver::TranslationResultsString;
use crate::webserver::{CodeChatForWeb, CodeMirror, SourceFileMetadata};

// ## Data structures
/// This enum contains the results of translating a source file to the CodeChat
/// Editor format.
#[derive(Debug, PartialEq)]
pub enum TranslationResults {
    // This file is unknown to and therefore not supported by the CodeChat
    // Editor.
    Unknown,
    // This is a CodeChat Editor file but it contains errors that prevent its
    // translation. The string contains the error message.
    Err(String),
    // A CodeChat Editor file; the struct contains the file's contents
    // translated to CodeMirror.
    CodeChat(CodeChatForWeb),
}

// On save, the process is CodeChatForWeb -> Vec\<CodeDocBlocks> -> source code.
//
// ## Globals
lazy_static! {
    /// Match the lexer directive in a source file.
    static ref LEXER_DIRECTIVE: Regex = Regex::new(r"CodeChat Editor lexer: (\w+)").unwrap();
}

static DOC_BLOCK_SEPARATOR_STRING: &str = "\n<CodeChatEditor-separator/>\n\n";

// ## Determine if the provided file is part of a project.
pub fn find_path_to_toc(file_path: &Path) -> Option<PathBuf> {
    // To determine if this source code is part of a project, look for a project
    // file by searching the current directory, then all its parents, for a file
    // named `toc.md`.
    let mut path_to_toc = PathBuf::new();
    let mut current_dir = file_path.to_path_buf();
    loop {
        let mut project_file = current_dir.clone();
        project_file.push("toc.md");
        if project_file.is_file() {
            path_to_toc.pop();
            path_to_toc.push("toc.md");
            return Some(path_to_toc);
        }
        if !current_dir.pop() {
            return None;
        }
        path_to_toc.push("../");
    }
}

// ## Transform `CodeChatForWeb` to source code
//
// This function takes in a source file in web-editable format
// (the `CodeChatForWeb` struct) and transforms it into source code.
pub fn codechat_for_web_to_source(
    // The file to save plus metadata, stored in the `LexedSourceFile`
    codechat_for_web: CodeChatForWeb,
    // Lexer info, needed to transform the `LexedSourceFile` into source code.
    language_lexers_compiled: &LanguageLexersCompiled,
) -> Result<String, String> {
    // Given the mode, find the lexer.
    let lexer: &std::sync::Arc<crate::lexer::LanguageLexerCompiled> = match language_lexers_compiled
        .map_mode_to_lexer
        .get(&codechat_for_web.metadata.mode)
    {
        Some(v) => v,
        None => return Err("Invalid mode".to_string()),
    };

    // Convert from `CodeMirror` to a `SortaCodeDocBlocks`.
    let code_doc_block_vec = code_mirror_to_code_doc_blocks(&codechat_for_web.source);
    code_doc_block_vec_to_source(code_doc_block_vec, lexer)
}

/// Translate from CodeMirror to CodeDocBlocks.
fn code_mirror_to_code_doc_blocks(code_mirror: &CodeMirror) -> Vec<CodeDocBlock> {
    let doc_blocks = &code_mirror.doc_blocks;
    // A CodeMirror "document" is really source code.
    let code = &code_mirror.doc;
    let mut code_doc_block_arr: Vec<CodeDocBlock> = Vec::new();
    // Keep track of the to index of the previous doc block. Since we haven't
    // processed any doc blocks, start at 0.
    let mut code_index: usize = 0;

    // Walk through each doc block, inserting the previous code block followed
    // by the doc block.
    for codemirror_doc_block in doc_blocks {
        // Append the code block, unless it's empty.
        let code_contents = &code[code_index..codemirror_doc_block.0];
        if !code_contents.is_empty() {
            code_doc_block_arr.push(CodeDocBlock::CodeBlock(code_contents.to_string()))
        }
        // Append the doc block.
        code_doc_block_arr.push(CodeDocBlock::DocBlock(DocBlock {
            indent: codemirror_doc_block.2.to_string(),
            delimiter: codemirror_doc_block.3.to_string(),
            contents: codemirror_doc_block.4.to_string(),
            lines: 0,
        }));
        code_index = codemirror_doc_block.1 + 1;
    }

    // See if there's a code block after the last doc block.
    let code_contents = &code[code_index..];
    if !code_contents.is_empty() {
        code_doc_block_arr.push(CodeDocBlock::CodeBlock(code_contents.to_string()));
    }

    code_doc_block_arr
}

// Turn this vec of CodeDocBlocks into a string of source code.
fn code_doc_block_vec_to_source(
    code_doc_block_vec: Vec<CodeDocBlock>,
    lexer: &LanguageLexerCompiled,
) -> Result<String, String> {
    let mut file_contents = String::new();
    for code_doc_block in code_doc_block_vec {
        match code_doc_block {
            CodeDocBlock::DocBlock(doc_block) => {
                // Append a doc block, adding a space between the opening
                // delimiter and the contents when necessary.
                let mut append_doc_block = |indent: &str, delimiter: &str, contents: &str| {
                    file_contents += indent;
                    file_contents += delimiter;
                    // Add a space between the delimiter and comment body,
                    // unless the comment was a newline or we're at the end of
                    // the file.
                    if contents.is_empty() || contents == "\n" {
                        // Nothing to append in this case.
                    } else {
                        // Put a space between the delimiter and the contents.
                        file_contents += " ";
                    }
                    file_contents += contents;
                };

                let is_inline_delim = lexer
                    .language_lexer
                    .inline_comment_delim_arr
                    .contains(&doc_block.delimiter);

                // Build a comment based on the type of the delimiter.
                if is_inline_delim {
                    // To produce an inline comment, split the contents into a
                    // series of lines, adding the indent and inline comment
                    // delimiter to each line.
                    for content_line in doc_block.contents.split_inclusive('\n') {
                        append_doc_block(&doc_block.indent, &doc_block.delimiter, content_line);
                    }
                } else {
                    // Block comments are more complex.
                    //
                    // First, determine the closing comment delimiter matching
                    // the provided opening delimiter.
                    let block_comment_closing_delimiter = match lexer
                        .language_lexer
                        .block_comment_delim_arr
                        .iter()
                        .position(|bc| bc.opening == doc_block.delimiter)
                    {
                        Some(index) => &lexer.language_lexer.block_comment_delim_arr[index].closing,
                        None => {
                            return Err(format!(
                                "Unknown comment opening delimiter '{}'.",
                                doc_block.delimiter
                            ))
                        }
                    };

                    // Then, split the contents into a series of lines. Build a
                    // properly-indented block comment around these lines.
                    let content_lines: Vec<&str> =
                        doc_block.contents.split_inclusive('\n').collect();
                    for (index, content_line) in content_lines.iter().enumerate() {
                        let is_last = index == content_lines.len() - 1;
                        // Process each line, based on its location (first/not
                        // first/last). Note that the first line can also be the
                        // last line in a one-line comment.
                        //
                        // On the last line, include a properly-formatted
                        // closing comment delimiter:
                        let content_line_updated = if is_last {
                            match content_line.strip_suffix('\n') {
                                // include a space then the closing delimiter
                                // before the final newline (if it exists; at
                                // the end of a file, it may not);
                                Some(stripped_line) => {
                                    stripped_line.to_string()
                                        + " "
                                        + &block_comment_closing_delimiter
                                        + "\n"
                                }
                                // otherwise (i.e. there's no final newline),
                                // just include a space and the closing
                                // delimiter.
                                None => {
                                    content_line.to_string()
                                        + " "
                                        + &block_comment_closing_delimiter
                                }
                            }
                        } else {
                            // Since this isn't the last line, don't include the
                            // closing comment delimiter.
                            content_line.to_string()
                        };

                        // On the first line, include the indent and opening
                        // delimiter.
                        let is_first = index == 0;
                        if is_first {
                            append_doc_block(
                                &doc_block.indent,
                                &doc_block.delimiter,
                                &content_line_updated,
                            );
                        // Since this isn't a first line:
                        } else {
                            // - If this line is just a newline, include just
                            //   the newline.
                            if *content_line == "\n" {
                                append_doc_block("", "", "\n");
                            // - Otherwise, include spaces in place of the
                            //   delimiter.
                            } else {
                                append_doc_block(
                                    &doc_block.indent,
                                    &" ".repeat(doc_block.delimiter.len()),
                                    &content_line_updated,
                                );
                            }
                        }
                    }
                }
            }

            CodeDocBlock::CodeBlock(contents) =>
            // This is code. Simply append it (by definition, indent and
            // delimiter are empty).
            {
                file_contents += &contents
            }
        }
    }
    Ok(file_contents)
}

// ## Transform from source code to `CodeChatForWeb`
//
// Given the contents of a file, classify it and (for CodeChat Editor files)
// convert it to the `CodeChatForWeb` format.
pub fn source_to_codechat_for_web(
    // The file's contents.
    file_contents: String,
    // The file's extension.
    file_ext: &str,
    // True if this file is a TOC.
    _is_toc: bool,
    // True if this file is part of a project.
    _is_project: bool,
    // Lexers.
    language_lexers_compiled: &LanguageLexersCompiled,
) -> TranslationResults {
    // Determine the lexer to use for this file.
    let lexer_name;
    // First, search for a lexer directive in the file contents.
    let lexer = if let Some(captures) = LEXER_DIRECTIVE.captures(&file_contents) {
        lexer_name = captures[1].to_string();
        match language_lexers_compiled.map_mode_to_lexer.get(&lexer_name) {
            Some(v) => v,
            None => {
                return TranslationResults::Err(format!(
                    "<p>Unknown lexer type {}.</p>",
                    &lexer_name
                ))
            }
        }
    } else {
        // Otherwise, look up the lexer by the file's extension.
        if let Some(llc) = language_lexers_compiled
            .map_ext_to_lexer_vec
            .get(&file_ext.to_string())
        {
            llc.first().unwrap()
        } else {
            // The file type is unknown; treat it as plain text.
            return TranslationResults::Unknown;
        }
    };

    // Transform the provided file into the `CodeChatForWeb` structure.
    let code_doc_block_arr;
    let codechat_for_web = CodeChatForWeb {
        metadata: SourceFileMetadata {
            mode: lexer.language_lexer.lexer_name.to_string(),
        },
        source: if lexer.language_lexer.lexer_name.as_str() == "markdown" {
            // Document-only files are easy: just encode the contents.
            let html = markdown_to_html(&file_contents);
            // TODO: process the HTML.
            CodeMirror {
                doc: html,
                doc_blocks: vec![],
            }
        } else {
            // This is a source file.
            //
            // Create an initially-empty struct; the source code will be
            // translated to this.
            let mut code_mirror = CodeMirror {
                doc: "".to_string(),
                doc_blocks: Vec::new(),
            };

            // Lex the code.
            code_doc_block_arr = source_lexer(&file_contents, lexer);

            // Combine all the doc blocks into a single string, separated by a
            // delimiter. Transform this to markdown, then split the transformed
            // content back into the doc blocks they came from. This is
            // necessary to allow references between doc blocks to work; for
            // example, `[Link][1]` in one doc block, then `[1]: http:/foo.org`
            // in another doc block requires both to be in the same Markdown
            // document to translate correctly.
            let mut doc_block_contents_vec: Vec<&str> = Vec::new();
            for code_or_doc_block in &code_doc_block_arr {
                if let CodeDocBlock::DocBlock(doc_block) = code_or_doc_block {
                    doc_block_contents_vec.push(&doc_block.contents);
                }
            }
            let combined_doc_blocks = &doc_block_contents_vec.join(DOC_BLOCK_SEPARATOR_STRING);
            let html = markdown_to_html(combined_doc_blocks);
            // Now that we have HTML, process it. TODO.
            //
            // After processing by Markdown, the double newline at the of the
            // doc block separate string becomes a single newline; split using
            // this slightly shorter string.
            doc_block_contents_vec = html
                .split(&DOC_BLOCK_SEPARATOR_STRING[0..DOC_BLOCK_SEPARATOR_STRING.len() - 1])
                .collect();

            // Translate each `CodeDocBlock` to its `CodeMirror` equivalent.
            let mut index = 0;
            for code_or_doc_block in code_doc_block_arr {
                match code_or_doc_block {
                    CodeDocBlock::CodeBlock(code_string) => code_mirror.doc.push_str(&code_string),
                    CodeDocBlock::DocBlock(doc_block) => {
                        // Create the doc block.
                        let len = code_mirror.doc.len();
                        code_mirror.doc_blocks.push((
                            // From
                            len,
                            // To. Make this one line short, which allows
                            // CodeMirror to correctly handle inserts at the
                            // first character of the following code block.
                            len + doc_block.lines - 1,
                            doc_block.indent.to_string(),
                            doc_block.delimiter.to_string(),
                            // Used the markdown-translated replacement for this
                            // doc block, rather than the original string.
                            doc_block_contents_vec[index].to_string(),
                        ));
                        index += 1;
                        // Append newlines to the document; the doc block will
                        // replace these in the editor. This keeps the line
                        // numbering of non-doc blocks correct.
                        code_mirror.doc.push_str(&"\n".repeat(doc_block.lines));
                    }
                }
            }
            code_mirror
        },
    };

    TranslationResults::CodeChat(codechat_for_web)
}

// Like `source_to_codechat_for_web`, translate a source file to the CodeChat
// Editor client format. This wraps a call to that function with additional
// processing (determine if this is part of a project, encode the output as
// necessary, etc.).
pub fn source_to_codechat_for_web_string(
    // The file's contents.
    file_contents: String,
    // The path to this file.
    file_path: &Path,
    // True if this file is a TOC.
    is_toc: bool,
    // Lexers.
    language_lexers_compiled: &LanguageLexersCompiled,
) -> (TranslationResultsString, Option<PathBuf>) {
    // Determine the file's extension, in order to look up a lexer.
    let ext = &file_path
        .extension()
        .unwrap_or_else(|| OsStr::new(""))
        .to_string_lossy();

    // To determine if this source code is part of a project, look for a project
    // file by searching the current directory, then all its parents, for a file
    // named `toc.md`.
    let path_to_toc = find_path_to_toc(file_path);
    let is_project = path_to_toc.is_some();

    (
        match source_to_codechat_for_web(
            file_contents,
            ext,
            is_toc,
            is_project,
            language_lexers_compiled,
        ) {
            TranslationResults::CodeChat(codechat_for_web) => {
                if is_toc {
                    // For the table of contents sidebar, which is pure
                    // markdown, just return the resulting HTML, rather than the
                    // editable CodeChat for web format.
                    TranslationResultsString::CodeChat(codechat_for_web.source.doc)
                } else {
                    // Otherwise, transform this data structure to JSON, so it
                    // can be sent to the CodeChat Editor Client.
                    match serde_json::to_string(&codechat_for_web) {
                        Ok(v) => TranslationResultsString::CodeChat(v),
                        Err(err) => TranslationResultsString::Err(err.to_string()),
                    }
                }
            }
            TranslationResults::Unknown => TranslationResultsString::Unknown,
            TranslationResults::Err(err) => TranslationResultsString::Err(err),
        },
        path_to_toc,
    )
}

/// Convert markdown to HTML. (This assumes the Markdown defined in the
/// CommonMark spec.)
fn markdown_to_html(markdown: &str) -> String {
    let mut options = Options::all();
    // Turndown (which converts HTML back to Markdown) doesn't support smart
    // punctuation.
    options.remove(Options::ENABLE_SMART_PUNCTUATION);
    let parser = Parser::new_ext(markdown, options);
    let mut html_output = String::new();
    html::push_html(&mut html_output, parser);
    html_output
}

// Goal: make it easy to update the data structure. We update on every
// load/save, then do some accesses during those processes.
//
// Top-level data structures: a file HashSet<PathBuf, FileAnchor> and an id
// HashMap<id, {Anchor, HashSet<referring_id>}>. Some FileAnchors in the file
// HashSet are also in a pending load list.
//
// - To update a file:
//   - Remove the old file from the file HasHMap. Add an empty FileAnchor to the
//     file HashMap.
//   - For each id, see if that id already exists.
//     - If the id exists: if it refers to an id in the old FileAnchor, replace
//       it with the new one. If not, need to perform resolution on this id (we
//       have a non-unique id; how to fix?).
//     - If the id doesn't exist: create a new one.
//   - For each hyperlink, see if that id already exists.
//     - If so, upsert the referring id. Check the metadata on the id to make
//       sure that data is current. If not, add this to the pending hyperlinks
//       list. If the file is missing, delete it from the cache.
//     - If not, create a new entry in the id HashSet and add the referring id
//       to the HashSet. Add the file to a pending hyperlinks list.
//   - When the file is processed:
//     - Look for all entries in the pending file list that refer to the current
//       file and resolve these. Start another task to load in all pending
//       files.
//     - Look at the old file; remove each id that's still in the id HashMap. If
//       the id was in the HashMap and it also was a Hyperlink, remove that from
//       the HashSet.
// - To remove a file from the HashMap:
//   - Remove it from the file HashMap.
//   - For each hyperlink, remove it from the HashSet of referring links (if
//     that id still exists).
//   - For each id, remove it from the id HashMap.
// - To add a file from the HashSet:
//   - Perform an update with an empty FileAnchor.
//
// Pending hyperlinks list: for each hyperlink,
//
// - check if the id is now current in the cache. If so, add the referring id to
//   the HashSet then move to the next hyperlink.
// - check if the file is now current in the cache. If not, load the file and
//   update the cache, then go to step 1.
// - The id was not found, even in the expected file. Add the hyperlink to a
//   broken links set?
//
// Global operations:
//
// - Scan all files, then perform add/upsert/removes based on differences with
//   the cache.
//
// Functions:
//
// - Upsert an Anchor.
// - Upsert a Hyperlink.
// - Upsert a file.
// - Remove a file.
/**
/// There are two types of files that can serve as an anchor: these are file
/// anchor targets.
enum FileAnchor {
    Plain(PlainFileAnchor),
    Html(HtmlFileAnchor),
}

/// This is the cached metadata for a file that serves as an anchor: perhaps an
/// image, a PDF, or a video.
struct PlainFileAnchor {
    /// A relative path to this file, rooted at the project's TOC.
    path: Rc<PathBuf>,
    /// The globally-unique anchor used to link to this file. It's generated
    /// based on hash of the file's contents, so that each file will have a
    /// unique identifier.
    anchor: String,
    /// Metadata captured when this data was cached. If it disagrees with the
    /// file's current state, then this cached data should be re=generated from
    /// the file.
    file_metadata: Metadata,
}

/// Cached metadata for an HTML file.
struct HtmlFileAnchor {
    /// The file containing this HTML.
    file_anchor: PlainFileAnchor,
    /// The TOC numbering of this file.
    numbering: Vec<Option<u32>>,
    /// The headings in this file.
    headings: Vec<HeadingAnchor>,
    /// Anchors which appear before the first heading.
    pre_anchors: Vec<NonHeadingAnchor>,
}

/// Cached metadata shared by both headings (which are also anchors) and
/// non-heading anchors.
struct AnchorCommon {
    /// The HTML file containing this anchor.
    html_file_anchor: Weak<FileAnchor>,
    /// The globally-unique anchor used to link to this object.
    anchor: String,
    /// The inner HTML of this anchor.
    inner_html: String,
    /// The hyperlink this anchor contains.
    hyperlink: Option<Rc<Hyperlink>>,
}

/// An anchor is defined only in these two places: the anchor source.
enum HtmlAnchor {
    Heading(HeadingAnchor),
    NonHeading(NonHeadingAnchor),
}

/// Cached metadata for a heading (which is always also an anchor).
struct HeadingAnchor {
    anchor_common: AnchorCommon,
    /// The numbering of this heading on the HTML file containing it.
    numbering: Vec<Option<u32>>,
    /// Non-heading anchors which appear after this heading but before the next
    /// heading.
    non_heading_anchors: Vec<NonHeadingAnchor>,
}

/// Cached metadata for a non-heading anchor.
struct NonHeadingAnchor {
    anchor_common: AnchorCommon,
    /// The heading this anchor appears after (unless it appears before the
    /// first heading in this file).
    parent_heading: Option<Weak<HeadingAnchor>>,
    /// A snippet of HTML preceding this anchor.
    pre_snippet: String,
    /// A snippet of HTML following this anchor.
    post_snippet: String,
    /// If this is a numbered item, the name of the numbering group it belongs
    /// to.
    numbering_group: Option<String>,
    /// If this is a numbered item, its number.
    number: u32,
}

/// An anchor can refer to any of these structs: these are all possible anchor
/// targets.
enum Anchor {
    Html(HtmlAnchor),
    File(FileAnchor),
}

/// The metadata for a hyperlink.
struct Hyperlink {
    /// The file this hyperlink refers to.
    file: PathBuf,
    /// The anchor this hyperlink refers to.
    html_anchor: String,
}

/// The value stored in the id HashMap.
struct AnchorVal {
    /// The target anchor this id refers to.
    anchor: Anchor,
    /// All hyperlinks which target this anchor.
    referring_links: Rc<HashSet<String>>,
}

// Given HTML, catalog all link targets and link-like items, ensuring that they
// have a globally unique id.
fn html_analyze(
    file_path: &Path,
    html: &str,
    mut file_map: HashMap<Rc<PathBuf>, Rc<FileAnchor>>,
    mut anchor_map: HashMap<Rc<String>, HashSet<AnchorVal>>,
) -> io::Result<String> {
    // Create the missing anchors:
    //
    // A missing file.
    let missing_html_file_anchor = Rc::new(FileAnchor::Html(HtmlFileAnchor {
        file_anchor: PlainFileAnchor {
            path: Rc::new(PathBuf::new()),
            anchor: "".to_string(),
            // TODO: is there some way to create generic/empty metadata?
            file_metadata: Path::new(".").metadata().unwrap(),
        },
        numbering: Vec::new(),
        headings: Vec::new(),
        pre_anchors: Vec::new(),
    }));
    // Define an anchor in this file.
    let missing_anchor = NonHeadingAnchor {
        anchor_common: AnchorCommon {
            html_file_anchor: Rc::downgrade(&missing_html_file_anchor),
            anchor: "".to_string(),
            hyperlink: None,
            inner_html: "".to_string(),
        },
        parent_heading: None,
        pre_snippet: "".to_string(),
        post_snippet: "".to_string(),
        numbering_group: None,
        number: 0,
    };
    // Add this to the top-level hashes.
    let anchor_val = AnchorVal {
        anchor: Anchor::Html(HtmlAnchor::NonHeading(missing_anchor)),
        referring_links: Rc::new(HashSet::new()),
    };
    //file_map.insert(mfa.file_anchor.path, missing_html_file_anchor);
    //let anchor_val_set: HashSet<AnchorVal> = HashSet::new();
    //anchor_val_set.insert(anchor_val);
    //anchor_map.insert(&mfa.file_anchor.anchor, anchor_val_set);

    Ok("".to_string())
}
*/

// ## Tests
#[cfg(test)]
mod tests {
    use super::TranslationResults;
    use crate::lexer::{
        compile_lexers, supported_languages::get_language_lexer_vec, CodeDocBlock, DocBlock,
    };
    use crate::processing::{
        code_doc_block_vec_to_source, code_mirror_to_code_doc_blocks, codechat_for_web_to_source,
        source_to_codechat_for_web,
    };
    use crate::webserver::{CodeChatForWeb, CodeMirror, CodeMirrorDocBlocks, SourceFileMetadata};

    // ### Utilities
    fn build_codechat_for_web<'a>(
        mode: &str,
        doc: &str,
        doc_blocks: CodeMirrorDocBlocks,
    ) -> CodeChatForWeb {
        // Wrap the provided parameters in the necessary data structures.
        CodeChatForWeb {
            metadata: SourceFileMetadata {
                mode: mode.to_string(),
            },
            source: CodeMirror {
                doc: doc.to_string(),
                doc_blocks,
            },
        }
    }

    // Provide a way to construct one element of the `CodeMirrorDocBlocks`
    // vector.
    fn build_codemirror_doc_block(
        start: usize,
        end: usize,
        indent: &str,
        delimiter: &str,
        contents: &str,
    ) -> (
        usize,
        usize,
        String,
        String,
        String,
    ) {
        (
            start,
            end,
            indent.to_string(),
            delimiter.to_string(),
            contents.to_string(),
        )
    }

    fn build_doc_block(indent: &str, delimiter: &str, contents: &str) -> CodeDocBlock {
        return CodeDocBlock::DocBlock(DocBlock {
            indent: indent.to_string(),
            delimiter: delimiter.to_string(),
            contents: contents.to_string(),
            lines: 0,
        });
    }

    fn build_code_block(contents: &str) -> CodeDocBlock {
        return CodeDocBlock::CodeBlock(contents.to_string());
    }

    fn run_test<'a>(mode: &str, doc: &str, doc_blocks: CodeMirrorDocBlocks) -> Vec<CodeDocBlock> {
        let codechat_for_web = build_codechat_for_web(mode, doc, doc_blocks);
        code_mirror_to_code_doc_blocks(&codechat_for_web.source)
    }

    // ### Tests for `codechat_for_web_to_source`
    //
    // Since it just invokes `code_mirror_to_code_doc_blocks` and
    // `code_doc_block_vec_to_source`, both of which have their own set of
    // tests, we just need to do a bit of testing.
    #[test]
    fn test_codechat_for_web_to_source() {
        let llc = compile_lexers(get_language_lexer_vec());

        let codechat_for_web = build_codechat_for_web("python", "", vec![]);
        assert_eq!(
            codechat_for_web_to_source(codechat_for_web, &llc),
            Result::Ok("".to_string())
        );

        let codechat_for_web = build_codechat_for_web("undefined", "", vec![]);
        assert_eq!(
            codechat_for_web_to_source(codechat_for_web, &llc),
            Result::Err("Invalid mode".to_string())
        );
    }

    // ### Tests for `code_mirror_to_code_doc_blocks`
    #[test]
    fn test_codemirror_to_code_doc_blocks_py() {
        // Pass nothing to the function.
        assert_eq!(run_test("python", "", vec![]), vec![]);

        // Pass one code block.
        assert_eq!(
            run_test("python", "Test", vec![]),
            vec![build_code_block("Test")]
        );

        // Pass one doc block.
        assert_eq!(
            run_test(
                "python",
                "\n",
                vec![build_codemirror_doc_block(0, 0, "", "#", "Test")],
            ),
            vec![build_doc_block("", "#", "Test")]
        );

        // A code block then a doc block
        assert_eq!(
            run_test(
                "python",
                "code\n\n",
                vec![build_codemirror_doc_block(5, 5, "", "#", "doc")],
            ),
            vec![build_code_block("code\n"), build_doc_block("", "#", "doc")]
        );

        // A doc block then a code block
        assert_eq!(
            run_test(
                "python",
                "\ncode\n",
                vec![build_codemirror_doc_block(0, 0, "", "#", "doc")],
            ),
            vec![build_doc_block("", "#", "doc"), build_code_block("code\n")]
        );

        // A code block, then a doc block, then another code block
        assert_eq!(
            run_test(
                "python",
                "\ncode\n\n",
                vec![
                    build_codemirror_doc_block(0, 0, "", "#", "doc 1"),
                    build_codemirror_doc_block(6, 6, "", "#", "doc 2")
                ],
            ),
            vec![
                build_doc_block("", "#", "doc 1"),
                build_code_block("code\n"),
                build_doc_block("", "#", "doc 2")
            ]
        );
    }

    #[test]
    fn test_codemirror_to_code_doc_blocks_cpp() {
        // Pass an inline comment.
        assert_eq!(
            run_test(
                "c_cpp",
                "\n",
                vec![build_codemirror_doc_block(0, 0, "", "//", "Test")]
            ),
            vec![build_doc_block("", "//", "Test")]
        );

        // Pass a block comment.
        assert_eq!(
            run_test(
                "c_cpp",
                "\n",
                vec![build_codemirror_doc_block(0, 0, "", "/*", "Test")]
            ),
            vec![build_doc_block("", "/*", "Test")]
        );

        // Two back-to-back doc blocks.
        assert_eq!(
            run_test(
                "c_cpp",
                "\n\n",
                vec![
                    build_codemirror_doc_block(0, 0, "", "//", "Test 1"),
                    build_codemirror_doc_block(1, 1, "", "/*", "Test 2")
                ]
            ),
            vec![
                build_doc_block("", "//", "Test 1"),
                build_doc_block("", "/*", "Test 2")
            ]
        );
    }

    // ### Tests for `code_doc_block_vec_to_source`
    //
    // A language with just one inline comment delimiter and no block comments.
    #[test]
    fn test_code_doc_blocks_to_source_py() {
        let llc = compile_lexers(get_language_lexer_vec());
        let py_lexer = llc.map_mode_to_lexer.get(&"python".to_string()).unwrap();

        // An empty document.
        assert_eq!(code_doc_block_vec_to_source(vec![], py_lexer).unwrap(), "");
        // A one-line comment.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "#", "Test")], py_lexer).unwrap(),
            "# Test"
        );
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "#", "Test\n")], py_lexer)
                .unwrap(),
            "# Test\n"
        );
        // Check empty doc block lines and multiple lines.
        assert_eq!(
            code_doc_block_vec_to_source(
                vec![build_doc_block("", "#", "Test 1\n\nTest 2")],
                py_lexer
            )
            .unwrap(),
            "# Test 1\n#\n# Test 2"
        );

        // Repeat the above tests with an indent.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block(" ", "#", "Test")], py_lexer)
                .unwrap(),
            " # Test"
        );
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("  ", "#", "Test\n")], py_lexer)
                .unwrap(),
            "  # Test\n"
        );
        assert_eq!(
            code_doc_block_vec_to_source(
                vec![build_doc_block("   ", "#", "Test 1\n\nTest 2")],
                py_lexer
            )
            .unwrap(),
            "   # Test 1\n   #\n   # Test 2"
        );

        // Basic code.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_code_block("Test")], py_lexer).unwrap(),
            "Test"
        );

        // An incorrect delimiter.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "?", "Test")], py_lexer)
                .unwrap_err(),
            "Unknown comment opening delimiter '?'."
        );
    }

    // A language with just one block comment delimiter and no inline comment
    // delimiters.
    #[test]
    fn test_code_doc_blocks_to_source_css() {
        let llc = compile_lexers(get_language_lexer_vec());
        let css_lexer = llc.map_mode_to_lexer.get(&"css".to_string()).unwrap();

        // An empty document.
        assert_eq!(code_doc_block_vec_to_source(vec![], css_lexer).unwrap(), "");
        // A one-line comment.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "/*", "Test\n")], css_lexer)
                .unwrap(),
            "/* Test */\n"
        );
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "/*", "Test")], css_lexer)
                .unwrap(),
            "/* Test */"
        );
        // Check empty doc block lines and multiple lines.
        assert_eq!(
            code_doc_block_vec_to_source(
                vec![
                    build_code_block("Test_0\n"),
                    build_doc_block("", "/*", "Test 1\n\nTest 2\n")
                ],
                css_lexer
            )
            .unwrap(),
            r#"Test_0
/* Test 1

   Test 2 */
"#
        );

        // Repeat the above tests with an indent.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("  ", "/*", "Test\n")], css_lexer)
                .unwrap(),
            "  /* Test */\n"
        );
        assert_eq!(
            code_doc_block_vec_to_source(
                vec![
                    build_code_block("Test_0\n"),
                    build_doc_block("   ", "/*", "Test 1\n\nTest 2\n")
                ],
                css_lexer
            )
            .unwrap(),
            r#"Test_0
   /* Test 1

      Test 2 */
"#
        );

        // Basic code.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_code_block("Test")], css_lexer).unwrap(),
            "Test"
        );

        // An incorrect delimiter.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "?", "Test")], css_lexer)
                .unwrap_err(),
            "Unknown comment opening delimiter '?'."
        );
    }

    // A language with multiple inline and block comment styles.
    #[test]
    fn test_code_doc_blocks_to_source_csharp() {
        let llc = compile_lexers(get_language_lexer_vec());
        let csharp_lexer = llc.map_mode_to_lexer.get(&"csharp".to_string()).unwrap();

        // An empty document.
        assert_eq!(
            code_doc_block_vec_to_source(vec![], csharp_lexer).unwrap(),
            ""
        );

        // An invalid comment.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "?", "Test\n")], csharp_lexer)
                .unwrap_err(),
            "Unknown comment opening delimiter '?'."
        );

        // Inline comments.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "//", "Test\n")], csharp_lexer)
                .unwrap(),
            "// Test\n"
        );
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "///", "Test\n")], csharp_lexer)
                .unwrap(),
            "/// Test\n"
        );

        // Block comments.
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "/*", "Test\n")], csharp_lexer)
                .unwrap(),
            "/* Test */\n"
        );
        assert_eq!(
            code_doc_block_vec_to_source(vec![build_doc_block("", "/**", "Test\n")], csharp_lexer)
                .unwrap(),
            "/** Test */\n"
        );
    }

    // ### Tests for `source_to_codechat_for_web`
    //
    // TODO.
    #[test]
    fn test_source_to_codechat_for_web_1() {
        let llc = compile_lexers(get_language_lexer_vec());

        // A file with an unknown extension and no lexer, which is classified as
        // a text file.
        assert_eq!(
            source_to_codechat_for_web("".to_string(), ".xxx", false, false, &llc),
            TranslationResults::Unknown
        );

        // A file with an invalid lexer specification. Obscure this, so that
        // this file can be successfully lexed by the CodeChat editor.
        let lexer_spec = format!("{}{}", "CodeChat Editor ", "lexer: ");
        assert_eq!(
            source_to_codechat_for_web(
                format!("{}unknown", lexer_spec),
                ".xxx",
                false,
                false,
                &llc
            ),
            TranslationResults::Err("<p>Unknown lexer type unknown.</p>".to_string())
        );

        // A CodeChat Editor document via filename.
        assert_eq!(
            source_to_codechat_for_web("".to_string(), "md", false, false, &llc),
            TranslationResults::CodeChat(build_codechat_for_web("markdown", "", vec![]))
        );

        // A CodeChat Editor document via lexer specification.
        assert_eq!(
            source_to_codechat_for_web(
                format!("{}markdown", lexer_spec),
                "xxx",
                false,
                false,
                &llc
            ),
            TranslationResults::CodeChat(build_codechat_for_web(
                "markdown",
                &format!("<p>{}markdown</p>\n", lexer_spec),
                vec![]
            ))
        );

        // An empty source file.
        assert_eq!(
            source_to_codechat_for_web("".to_string(), "js", false, false, &llc),
            TranslationResults::CodeChat(build_codechat_for_web("javascript", "", vec![]))
        );

        // A zero doc block source file.
        assert_eq!(
            source_to_codechat_for_web("let a = 1;".to_string(), "js", false, false, &llc),
            TranslationResults::CodeChat(build_codechat_for_web(
                "javascript",
                "let a = 1;",
                vec![]
            ))
        );

        // One doc block source files.
        assert_eq!(
            source_to_codechat_for_web("// Test".to_string(), "js", false, false, &llc),
            TranslationResults::CodeChat(build_codechat_for_web(
                "javascript",
                "\n",
                vec![build_codemirror_doc_block(0, 0, "", "//", "<p>Test</p>\n")]
            ))
        );
        assert_eq!(
            source_to_codechat_for_web("let a = 1;\n// Test".to_string(), "js", false, false, &llc),
            TranslationResults::CodeChat(build_codechat_for_web(
                "javascript",
                "let a = 1;\n\n",
                vec![build_codemirror_doc_block(
                    11,
                    11,
                    "",
                    "//",
                    "<p>Test</p>\n"
                )]
            ))
        );
        assert_eq!(
            source_to_codechat_for_web("// Test\nlet a = 1;".to_string(), "js", false, false, &llc),
            TranslationResults::CodeChat(build_codechat_for_web(
                "javascript",
                "\nlet a = 1;",
                vec![build_codemirror_doc_block(0, 0, "", "//", "<p>Test</p>\n")]
            ))
        );

        // A two doc block source file.
        assert_eq!(
            source_to_codechat_for_web(
                "// [Link][1]\nlet a = 1;\n/* [1]: http://b.org */".to_string(),
                "js",
                false,
                false,
                &llc
            ),
            TranslationResults::CodeChat(build_codechat_for_web(
                "javascript",
                "\nlet a = 1;\n\n",
                vec![
                    build_codemirror_doc_block(
                        0,
                        0,
                        "",
                        "//",
                        "<p><a href=\"http://b.org\">Link</a></p>"
                    ),
                    build_codemirror_doc_block(12, 12, "", "/*", "")
                ]
            ))
        );
    }
}
