"""
MongoNeo query builder module that provides a fluent query interface.

This module provides classes for building MongoDB queries with a
LINQ-like syntax, allowing for intuitive field expressions.
"""

import types
import inspect

__all__ = [
    "QueryBuilder",
    "QueryExpression",
    "QueryField",
    "enhance_model_class",
    "AndExpression",
    "OrExpression",
    "and_",
    "or_",
]


class QueryExpression:
    """Represents a query expression used for filtering documents."""

    def __init__(self, field_name, operator, value):
        self.field_name = field_name
        self.operator = operator
        self.value = value

    def to_mongo_query(self):
        """Convert the expression to a MongoDB query dict."""
        if self.operator == "eq":
            return {self.field_name: self.value}
        elif self.operator == "ne":
            return {self.field_name: {"$ne": self.value}}
        elif self.operator == "gt":
            return {self.field_name: {"$gt": self.value}}
        elif self.operator == "gte":
            return {self.field_name: {"$gte": self.value}}
        elif self.operator == "lt":
            return {self.field_name: {"$lt": self.value}}
        elif self.operator == "lte":
            return {self.field_name: {"$lte": self.value}}
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")

    def to_query_kwargs(self):
        """Convert the expression to MongoNeo query kwargs."""
        if self.operator == "eq":
            return {self.field_name: self.value}
        elif self.operator == "ne":
            return {f"{self.field_name}__ne": self.value}
        elif self.operator == "gt":
            return {f"{self.field_name}__gt": self.value}
        elif self.operator == "gte":
            return {f"{self.field_name}__gte": self.value}
        elif self.operator == "lt":
            return {f"{self.field_name}__lt": self.value}
        elif self.operator == "lte":
            return {f"{self.field_name}__lte": self.value}
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")

    def __and__(self, other):
        """Combine with another expression using AND logic (& operator)."""
        return AndExpression(self, other)

    def __or__(self, other):
        """Combine with another expression using OR logic (| operator)."""
        return OrExpression(self, other)

    def __bool__(self):
        """Allow for truth value testing, needed for Python's 'and' and 'or' operators.

        We always return True so that the second operand is evaluated, allowing
        us to capture both sides of logical operations.
        """
        return True

    def __rand__(self, other):
        """Support right-sided AND operations (other & self)."""
        return AndExpression(other, self)

    def __ror__(self, other):
        """Support right-sided OR operations (other | self)."""
        return OrExpression(other, self)


class CompoundExpression:
    """Base class for compound expressions (AND, OR)."""

    def __init__(self, left_expression, right_expression):
        self.left_expression = left_expression
        self.right_expression = right_expression

    def __bool__(self):
        """Allow for truth value testing."""
        return True

    def to_mongo_query(self):
        """Convert the compound expression to a MongoDB query dict."""
        raise NotImplementedError("Subclasses must implement this method")

    def to_query_kwargs(self):
        """Convert the compound expression to MongoNeo query kwargs."""
        raise NotImplementedError("Subclasses must implement this method")

    def __and__(self, other):
        """Combine with another expression using AND logic."""
        return AndExpression(self, other)

    def __or__(self, other):
        """Combine with another expression using OR logic."""
        return OrExpression(self, other)

    def __rand__(self, other):
        """Support right-sided AND operations."""
        return AndExpression(other, self)

    def __ror__(self, other):
        """Support right-sided OR operations."""
        return OrExpression(other, self)


class AndExpression(CompoundExpression):
    """Represents a logical AND between two query expressions."""

    def to_mongo_query(self):
        """Convert the AND expression to a MongoDB query dict."""
        left_query = self.left_expression.to_mongo_query()
        right_query = self.right_expression.to_mongo_query()

        # Handle nested $and operators by flattening
        if "$and" in left_query and "$and" not in right_query:
            return {"$and": left_query["$and"] + [right_query]}
        elif "$and" in right_query and "$and" not in left_query:
            return {"$and": [left_query] + right_query["$and"]}
        elif "$and" in left_query and "$and" in right_query:
            return {"$and": left_query["$and"] + right_query["$and"]}
        else:
            return {"$and": [left_query, right_query]}

    def to_query_kwargs(self):
        """Convert the AND expression to MongoNeo query kwargs."""
        # For AND operations, we can just merge the dictionaries
        # as MongoNeo handles them implicitly
        kwargs = {}
        kwargs.update(self.left_expression.to_query_kwargs())
        kwargs.update(self.right_expression.to_query_kwargs())
        return kwargs


class OrExpression(CompoundExpression):
    """Represents a logical OR between two query expressions."""

    def to_mongo_query(self):
        """Convert the OR expression to a MongoDB query dict."""
        left_query = self.left_expression.to_mongo_query()
        right_query = self.right_expression.to_mongo_query()

        # Handle nested $or operators by flattening
        if "$or" in left_query and "$or" not in right_query:
            return {"$or": left_query["$or"] + [right_query]}
        elif "$or" in right_query and "$or" not in left_query:
            return {"$or": [left_query] + right_query["$or"]}
        elif "$or" in left_query and "$or" in right_query:
            return {"$or": left_query["$or"] + right_query["$or"]}
        else:
            return {"$or": [left_query, right_query]}

    def to_query_kwargs(self):
        """Convert the OR expression to MongoNeo query kwargs.

        For OR operations, MongoNeo uses the Q object, but since we don't have
        that here, we'll just return a dictionary with the $or operator.
        """
        return {
            "$or": [
                self.left_expression.to_query_kwargs(),
                self.right_expression.to_query_kwargs(),
            ]
        }


# Utility functions for constructing expressions
def and_(*expressions):
    """Create an AND expression from multiple expressions."""
    return AndExpression(*expressions)


def or_(*expressions):
    """Create an OR expression from multiple expressions."""
    return OrExpression(*expressions)


class QueryBuilder:
    """A fluent interface for building MongoDB queries."""

    def __init__(self, document_class):
        self.document_class = document_class
        self.expressions = []

    def where(self, expression):
        """Add a filter expression to the query."""
        self.expressions.append(expression)
        return self

    def to_queryset(self):
        """Convert the builder to a QuerySet for execution."""
        # Import ReferenceField here to avoid circular imports
        from mongoneo.fields import ReferenceField

        # Use the document class's objects manager to get a QuerySet
        queryset = self.document_class.objects

        if not self.expressions:
            return queryset

        # Check if any expressions reference other documents through reference fields
        ref_paths = {}  # Maps reference field name to referenced document type
        for expr in self.expressions:
            if isinstance(expr, CompoundExpression):
                self._extract_ref_paths(expr.left_expression, ref_paths)
                self._extract_ref_paths(expr.right_expression, ref_paths)
            elif "." in expr.field_name:
                parts = expr.field_name.split(".")
                ref_field_name = parts[0]
                try:
                    field = getattr(self.document_class, ref_field_name)
                    if isinstance(field, ReferenceField):
                        ref_paths[ref_field_name] = field.document_type
                except (AttributeError, KeyError):
                    pass  # Not a reference field

        if ref_paths:
            # We have reference fields, so we need to use an aggregation pipeline
            # to first $lookup the referenced documents and then filter
            pipeline = []

            # Add lookup stages for all referenced document types
            for ref_field, ref_doc_type in ref_paths.items():
                pipeline.append(
                    {
                        "$lookup": {
                            "from": ref_doc_type._get_collection_name(),
                            "localField": ref_field,
                            "foreignField": "_id",
                            "as": f"__{ref_field}",
                        }
                    }
                )
                # Unwind the array (since lookup returns an array)
                pipeline.append(
                    {
                        "$unwind": {
                            "path": f"$__{ref_field}",
                            "preserveNullAndEmptyArrays": True,
                        }
                    }
                )

            # Now build the match condition
            match_condition = self._build_aggregation_match()
            if match_condition:
                pipeline.append({"$match": match_condition})

            # Execute the aggregation pipeline
            return queryset.aggregate(pipeline)
        else:
            # No reference fields, use normal query
            query_dict = self._build_query()
            queryset = queryset.filter(**query_dict)

        return queryset

    def _extract_ref_paths(self, expr, ref_paths):
        """Extract reference field paths from an expression."""
        # Import ReferenceField here to avoid circular imports
        from mongoneo.fields import ReferenceField

        if not hasattr(expr, "field_name"):
            return

        if "." in expr.field_name:
            parts = expr.field_name.split(".")
            ref_field_name = parts[0]
            try:
                field = getattr(self.document_class, ref_field_name)
                if isinstance(field, ReferenceField):
                    ref_paths[ref_field_name] = field.document_type
            except (AttributeError, KeyError):
                pass  # Not a reference field

    def _build_aggregation_match(self):
        """Build a MongoDB $match stage for aggregation pipeline."""
        # Import ReferenceField here to avoid circular imports
        from mongoneo.fields import ReferenceField

        match_condition = {}

        # Helper function to rewrite field paths for references
        def rewrite_field_path(field_path):
            if "." in field_path:
                parts = field_path.split(".")
                ref_field = parts[0]
                rest_of_path = ".".join(parts[1:])

                try:
                    # Check if this is indeed a reference field
                    field = getattr(self.document_class, ref_field)
                    if isinstance(field, ReferenceField):
                        # Rewrite to use the lookup result
                        return f"__{ref_field}.{rest_of_path}"
                except (AttributeError, KeyError):
                    pass  # Not a reference field, leave as is
            return field_path

        # Helper function to rewrite reference fields in a query dictionary
        def rewrite_query_dict(query_dict):
            if not isinstance(query_dict, dict):
                return query_dict

            new_dict = {}
            for k, v in query_dict.items():
                if k in ("$and", "$or"):
                    # Recursively handle logical operators
                    new_dict[k] = [rewrite_query_dict(sub_dict) for sub_dict in v]
                elif "." in k:
                    # Rewrite field path
                    new_key = rewrite_field_path(k)
                    new_dict[new_key] = v
                elif k.startswith("$"):
                    # Pass through MongoDB operators
                    new_dict[k] = v
                else:
                    # Check if it needs to be rewritten
                    new_key = rewrite_field_path(k)
                    if isinstance(v, dict):
                        # If value is a dict (e.g., for $gt, $lt operators), recursively rewrite it
                        new_dict[new_key] = rewrite_query_dict(v)
                    else:
                        new_dict[new_key] = v
            return new_dict

        for expr in self.expressions:
            if isinstance(expr, CompoundExpression):
                # For compound expressions, use the mongo query directly
                mongo_query = expr.to_mongo_query()
                # Rewrite field paths in the mongo query
                mongo_query = rewrite_query_dict(mongo_query)

                if match_condition:
                    if "$and" in match_condition:
                        match_condition["$and"].append(mongo_query)
                    else:
                        match_condition = {"$and": [match_condition, mongo_query]}
                else:
                    match_condition = mongo_query
            else:
                field_name = expr.field_name
                operator = expr.operator
                value = expr.value

                # Rewrite field path if it's a reference field
                field_name = rewrite_field_path(field_name)

                # Build the appropriate operator expression
                if operator == "eq":
                    field_expr = {field_name: value}
                elif operator == "ne":
                    field_expr = {field_name: {"$ne": value}}
                elif operator == "gt":
                    field_expr = {field_name: {"$gt": value}}
                elif operator == "gte":
                    field_expr = {field_name: {"$gte": value}}
                elif operator == "lt":
                    field_expr = {field_name: {"$lt": value}}
                elif operator == "lte":
                    field_expr = {field_name: {"$lte": value}}
                else:
                    raise ValueError(f"Unsupported operator: {operator}")

                # Add to match condition
                if match_condition:
                    if "$and" in match_condition:
                        match_condition["$and"].append(field_expr)
                    else:
                        match_condition = {"$and": [match_condition, field_expr]}
                else:
                    match_condition = field_expr

        return match_condition

    def __iter__(self):
        """Make the builder iterable by returning an iterator from the QuerySet."""
        return iter(self.to_queryset())

    def __getitem__(self, key):
        """Allow indexing/slicing by proxying to the QuerySet."""
        return self.to_queryset()[key]

    def __len__(self):
        """Get the length by proxying to the QuerySet."""
        return len(self.to_queryset())

    def _convert_field_path_to_mongo_format(self, field_path):
        """Converts dot notation field paths to MongoDB's double underscore notation."""
        if "." in field_path:
            return field_path.replace(".", "__")
        return field_path

    # Add helper methods for direct field access
    def __getattr__(self, name):
        """Access fields directly from the query builder.

        This allows for patterns like: User.query.name == "John"
        """
        return getattr(self.fields, name)

    # Helper method for working with relationships
    def related(self, field_name, related_query):
        """Find documents related to the results of another query.

        Args:
            field_name: The reference field that connects the documents
            related_query: A QueryBuilder, QuerySet or list of documents

        Returns:
            self for method chaining
        """
        # If it's a QueryBuilder, convert to a queryset
        if isinstance(related_query, QueryBuilder):
            related_queryset = related_query.to_queryset()
        # If it's a list of documents, extract the IDs
        elif isinstance(related_query, list) and len(related_query) > 0:
            if hasattr(related_query[0], "id"):
                related_ids = [doc.id for doc in related_query]
                self.expressions.append({f"{field_name}__in": related_ids})
                return self
            else:
                raise TypeError("Expected a list of documents with 'id' attributes")
        # Otherwise, assume it's a queryset
        else:
            related_queryset = related_query

        # Get the IDs from the related queryset
        related_ids = [doc.id for doc in related_queryset]

        # If there are no related IDs, return a query that will give no results
        if not related_ids:
            self.expressions.append({f"{field_name}__in": []})  # Force empty results
            return self

        # Create a new filter for the related IDs
        self.expressions.append({f"{field_name}__in": related_ids})

        return self

    def _build_query(self):
        """Build a MongoDB query from the expressions."""
        query_dict = {}

        for expr in self.expressions:
            if isinstance(expr, CompoundExpression):
                # For compound expressions, use the MongoDB raw query format
                mongo_query = expr.to_mongo_query()
                query_dict["__raw__"] = mongo_query
            else:
                # Handle simple expressions
                field_name = expr.field_name.replace(".", "__")
                operator = expr.operator
                value = expr.value

                if operator == "eq":
                    query_dict[field_name] = value
                else:
                    mongo_op = f"{field_name}__{operator}"
                    query_dict[mongo_op] = value

        return query_dict


class QueryDescriptor:
    """Descriptor that returns a new QueryBuilder instance for each access."""

    def __init__(self, cls):
        self.cls = cls

    def __get__(self, obj, objtype=None):
        """Called when the descriptor is accessed."""
        return QueryBuilder(self.cls)


def enhance_model_class(cls):
    """Add query capabilities to the model class."""
    # Add the query descriptor to the class
    cls.query = QueryDescriptor(cls)

    return cls
