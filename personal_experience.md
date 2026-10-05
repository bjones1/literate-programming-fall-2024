## Personal experience

Here are examples of Git situations that confused me/caused me to
struggle/didn't do what I expected:

- (jhg246) When starting out with git it can be very easy to make a mess of a
  repository if you don't understand how to navigate branches and merges. This
  happened to me and it was very confusing and frustrating. The solution was to
  use ' git reset ' to return to a version of the repository that was
  functional. Maybe we could warn the user if they are in a branch that has no
  remote source and they are making changes/staging changes?

- (sbe80) I had a lot of confusion regarding conflicts. There's many ways to fix
  them and all are potential confusion points. Another thing I found confusing
  initially was when to keep files local and when to add them to the remote repo
  and how to properly navigate that.

- (ewj55) I tend to be uncertain about whether the changes I made are local or
  pushed to the remote repository. If someone is editing shared code, they
  should be clearly aware of whether their changes are local-only or affecting
  the upstream repo.

- (drj228) When creating a branch in VS Code, I was unsure whether I had created
  a local branch or a remote branch. I also did not understand that creating a
  local branch does not automatically publish it to GitHub. A hint explaining
  where the branch exists and whether it has an upstream branch would help me
  understand the next step.

- (ams2083) I didn't realize how difficult it would be to navigate a repository
  when you have dozens of people working and making changes. It's hard for me to
  remember what I'm working on and altering when I also have to take into
  account the additions of other people.

- (jit45) I have been unsure whether the branch I was working on had the newest
  changes from the remote repository before I started editing. In a shared
  repository, this made me worry that I might be changing an outdated version
  and create avoidable conflicts. A hint showing whether my branch is behind the
  remote would make that state clearer before I begin working.

- (raf322) For me, one of the things I have struggled with getting used to doing
  is stashing changes and keeping track of them. There have been times where I
  have been working on a project, trying to keep track of which stash has the
  changes I want to implement, and then giving up and not using stashes at all
  when it becomes clear that the stash I'm looking for isn't the one I've
  selected.
