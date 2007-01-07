#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

"""This class integrates all patches to optparse.py into an extended version
needed to provide processing of optional option arguments and option negation.

The extension is tested with optparse 1.5a2 and 1.5.3 (Python 2.4.4 and 2.5.0)
and should be used unless the author of optparse integrates the provided
patches into the main optparse.

"""

from optparse import Option, OptionError, OptionParser, __version__ as optparse_version, _


class OptionalOption(Option):
    """Patch to Option which allows optional option arguments and negation."""

    def _check_nargs(self):
        try:
            Option._check_nargs(self)
        except OptionError:
            if self.action not in ["store_true", "store_false"]:
                raise

    def _check_dest(self):
        Option._check_dest(self)
        if self.negate is None:
            self.negate = False

    def convert_value(self, opt, value):
        if value is not None:
            if (self.nargs or 0 + self.oargs or 0) == 1:
                return self.check_value(opt, value)
        return Option.convert_value(self, opt, value)

    def take_action(self, action, dest, opt, value, values, parser):
        if action in ["store_true", "store_false"]:
            _value = (action == "store_true") ^ self.negate
            if value is not None and (self.nargs or self.oargs):
                _value = [_value]
                if isinstance(value, tuple):
                    _value.extend(value)
                else:
                    _value.append(value)
                setattr(values, dest, tuple(_value))
            else:
                setattr(values, dest, _value)
            return 1
        return Option.take_action(self, action, dest, opt, value, values, parser)


    # this is a general version to add all overwritten _check_ methods
    l = locals()
    Option.CHECK_METHODS = [f.__name__ in l and l[f.__name__] or f
                            for i, f in enumerate(Option.CHECK_METHODS)]
    for a, f in l.items():
        if a.startswith('_check_') and f not in Option.CHECK_METHODS:
            Option.CHECK_METHODS.append(f)

    for a in ['oargs','negate']:
        if not a in Option.ATTRS:
            Option.ATTRS.append(a)
    del a, f, l


class OptionalOptionParser(OptionParser):
    """Patch to OptionParser which allows optional arguments and negation."""

    def __init__(self, usage=None, option_list=None, option_class=Option,
                             version=None, conflict_handler="error", description=None,
                             formatter=None, add_help_option=True, prog=None):
        if option_class is Option:
            option_class = OptionalOption
        kwargs = locals()
        del kwargs['self']
        OptionParser.__init__(self, **kwargs)

    def _match_long_opt(self, opt):
        if opt.startswith("--no-") and "--" + opt[5:] in self._long_opt:
            return ("--" + opt[5:], True)
        return OptionParser._match_long_opt(self, opt)

    def _process_long_opt(self, rargs, values):
        arg = rargs.pop(0)

        # Value explicitly attached to arg?    Pretend it's the next
        # argument.
        if "=" in arg:
            (opt, next_arg) = arg.split("=", 1)
            rargs.insert(0, next_arg)
            had_explicit_value = True
        else:
            opt = arg
            had_explicit_value = False

        opt = self._match_long_opt(opt)
        if isinstance(opt, tuple):
            negate = opt[1]
            opt = opt[0]
        else:
            negate = False
        option = self._long_opt[opt]
        option.negate ^= negate
        nargs = option.nargs or 0
        oargs = option.oargs or 0
        if option.takes_value() or nargs or oargs:
            oargs += nargs
            args = self._get_arguments(rargs)
            if len(args) < nargs:
                if nargs == 1:
                    self.error(_("%s option requires an argument") % opt)
                else:
                    self.error(_("%s option requires %d arguments")
                                 % (opt, nargs))
            elif len(args) == 0 or oargs == 0:
                value = None
            elif len(args) == 1 or oargs == 1:
                value = rargs.pop(0)
            else:
                value = tuple(rargs[0:oargs])
                del rargs[0:oargs]

        elif had_explicit_value:
            self.error(_("%s option does not take a value") % opt)

        else:
            value = None

        option.process(opt, value, values, self)


    def _process_short_opts(self, rargs, values):
        arg = rargs.pop(0)
        stop = False
        i = 1
        for ch in arg[1:]:
            opt = "-" + ch
            option = self._short_opt.get(opt)
            i += 1                        # we have consumed a character

            if not option:
                if optparse_version >= '1.5.3':
                    raise BadOptionError(opt)
                else:
                   self.error(_("no such option: %s") % opt)

            nargs = option.nargs or 0
            oargs = option.oargs or 0
            if option.takes_value() or nargs or oargs:
                # Any characters left in arg?    Pretend they're the
                # next arg, and stop consuming characters of arg.
                if i < len(arg):
                    rargs.insert(0, arg[i:])
                    stop = True

                oargs += nargs
                args = self._get_arguments(rargs)
                if len(args) < nargs:
                    if nargs == 1:
                        self.error(_("%s option requires an argument") % opt)
                    else:
                        self.error(_("%s option requires %d arguments")
                                             % (opt, nargs))
                elif len(args) == 0 or oargs == 0:
                    value = None
                elif len(args) == 1 or oargs == 1:
                    value = rargs.pop(0)
                else:
                    value = tuple(rargs[0:oargs])
                    del rargs[0:oargs]

            else:                         # option doesn't take a value
                value = None

            option.process(opt, value, values, self)

            if stop:
                break


    def is_true(self, opt_value):
        """Return True if the (optional) boolean option value is True."""
        return isinstance(opt_value, tuple) and opt_value[0] or opt_value


    def _is_opt(self, opt):
        """Return True if opt is a known short or long option."""

        # TODO: raise BadOptionError for unknown option
        if len(opt) < 2 or opt[0] != '-':
            return False
        if opt[1] != '-':
            return self._short_opt.get(opt[0:2]) is not None
        try:
            if "=" in opt:
                (opt, next_arg) = opt.split("=", 1)
            if self._match_long_opt(opt):
                return True
        except:
            pass

        return False


    def _get_arguments(self, rargs):
        """Return list of the first rargs items which aren't known options."""

        args = []
        i = 0
        count = len(rargs)
        while i < count and not self._is_opt(rargs[i]):
            args.append(rargs[i])
            i += 1

        return args
