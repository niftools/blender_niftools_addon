""" Nif Utilities, stores logging across the code base"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2016, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
# 
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import logging


class _MockOperator:
    def report(self, level, message):
        print(str(level) + ": " + message)


class NifLog:
    """A simple custom exception class for export errors. This module require initialisation of an operator reference to function."""  
    
    # Injectable operator reference used to perform reporting, default to simple logging
    op = _MockOperator()

    @staticmethod
    def debug(message):
        """Report a debug message."""
        NifLog.op.report({'DEBUG'}, message)

    @staticmethod
    def info(message):
        """Report an informative message."""
        NifLog.op.report({'INFO'}, message)

    @staticmethod
    def warn(message):
        """Report a warning message."""
        NifLog.op.report({'WARNING'}, message)

    @staticmethod
    def error(message):
        """Report an error and return ``{'FINISHED'}``. To be called by
        the :meth:`execute` method, as::

            return error('Something went wrong.')

        Blender will raise an exception that is passed to the caller.

        .. seealso::

            The :ref:`error reporting <dev-design-error-reporting>` design.
        """
        NifLog.op.report({'ERROR'}, message)
        return {'FINISHED'}
    
    @staticmethod
    def init(operator):
        NifLog.op = operator
        log_level_num = getattr(logging, operator.properties.log_level)
        logging.getLogger("niftools").setLevel(log_level_num)
        logging.getLogger("pyffi").setLevel(log_level_num)
