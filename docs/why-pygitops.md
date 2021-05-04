# Why pygitops?

## Alternatives

### GitPython

Pygitops extensively uses and owes a debt of gratitude to the GitPython package ([pypi](https://pypi.org/project/GitPython/), [github](https://github.com/gitpython-developers/GitPython).

#### Differences

What is the difference between GitPython and pygitops?

The primary difference between GitPython and pygitops is one of generalization.
GitPython has, relative to pygitops, a small amount of generalization. It provides relatively low-level access to git functions and objects.
Pygitops has a relatively large amount of generalization. It provides higher-level access to git functionality.

Another difference is that pygitops is built around operations (functions and [context managers](https://docs.python.org/3/reference/datamodel.html#context-managers)) while
GitPython takes a more object-oriented approach basing most of its functionality on objects and their methods.

#### Which to Choose?

Why would you want to choose GitPython or pygitops?

Obviously we, the creators of pygitops, are biased, but this is our advice:

If pygitops has the functionality you need... use it! If not, use GitPython (which is almost certain to have the functionality you need).

Because we have designed pygitops to be highly compatible with GitPython, you should not feel like you have to choose one or the other.
If you use pygitops, you will be using GitPython too, so you don't have to get "locked in" to pygitops; you can use pygitops as far as it can take you and
transfer to GitPython for the rest of your journey.

### Others?

Other than pygitops, there are very few maintained, high-level, git utility libraries we are aware of. As such, we started pygitops.
